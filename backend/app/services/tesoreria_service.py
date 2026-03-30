"""
Servicio de Tesorería
Contiene toda la lógica de negocio para gestión de tesorería
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.models.tesoreria import (
    Cheque, MovimientoTesoreria, CajaEfectivo, MovimientoCaja,
    MovimientoBancario, Gasto, Recibo,
    EstadoChequeEnum, OrigenChequeEnum, TipoChequeEnum, MetodoPagoEnum
)
from app.models.finanzas import CuentaBancaria
from app.models.empresa import Empresa
from app.models.cuenta_corriente import MovimientoCuentaCorriente, CobroCliente
from app.models.usuario import Usuario
from app.models.pesaje import Pesaje
from app.models.base import get_argentina_now
from app.schemas.tesoreria import (
    ChequeCreate, ChequeUpdate, DepositarChequeRequest, CobrarChequeRequest,
    RechazarChequeRequest, EntregarChequeRequest, MovimientoTesoreriaCreate,
    CajaEfectivoCreate, CajaEfectivoUpdate, MovimientoCajaCreate,
    CuentaBancariaCreate, CuentaBancariaUpdate, MovimientoBancarioCreate,
    GastoCreate, GastoUpdate, ReciboCreate, ResumenTesoreria, AnularMovimientoRequest
)


class TesoreriaService:
    """Servicio para gestión de tesorería"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CHEQUES ====================

    def get_cheques(
        self,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[str] = None,
        tipo: Optional[str] = None,
        origen: Optional[str] = None,
        empresa_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        buscar: Optional[str] = None,
        solo_en_cartera: bool = False,
        vencidos: bool = False,
        proximos_vencer: bool = False,
        dias_vencimiento: int = 7
    ) -> Dict[str, Any]:
        """Obtiene lista de cheques con filtros"""
        query = self.db.query(Cheque).filter(Cheque.activo == True)

        # Filtros
        if estado:
            query = query.filter(Cheque.estado == estado)
        elif solo_en_cartera:
            query = query.filter(Cheque.estado == EstadoChequeEnum.EN_CARTERA.value)

        if tipo:
            query = query.filter(Cheque.tipo == tipo)

        if origen:
            query = query.filter(Cheque.origen == origen)

        if empresa_id:
            query = query.filter(Cheque.empresa_id == empresa_id)

        if fecha_desde:
            query = query.filter(Cheque.fecha_vencimiento >= fecha_desde)

        if fecha_hasta:
            query = query.filter(Cheque.fecha_vencimiento <= fecha_hasta)

        if buscar:
            query = query.filter(
                or_(
                    Cheque.numero.ilike(f"%{buscar}%"),
                    Cheque.librador.ilike(f"%{buscar}%")
                )
            )

        if vencidos:
            query = query.filter(
                and_(
                    Cheque.fecha_vencimiento < date.today(),
                    Cheque.estado == EstadoChequeEnum.EN_CARTERA.value
                )
            )

        if proximos_vencer:
            fecha_limite = date.today() + timedelta(days=dias_vencimiento)
            query = query.filter(
                and_(
                    Cheque.fecha_vencimiento <= fecha_limite,
                    Cheque.fecha_vencimiento >= date.today(),
                    Cheque.estado == EstadoChequeEnum.EN_CARTERA.value
                )
            )

        # Total
        total = query.count()

        # Ordenar y paginar
        query = query.order_by(Cheque.fecha_vencimiento.asc())
        cheques = query.offset(skip).limit(limit).all()

        # Enriquecer datos
        items = [self._enrich_cheque(c) for c in cheques]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    def get_cheque(self, cheque_id: UUID) -> Optional[Cheque]:
        """Obtiene un cheque por ID"""
        return self.db.query(Cheque).filter(
            Cheque.id == cheque_id,
            Cheque.activo == True
        ).first()

    def create_cheque(self, data: ChequeCreate, registrado_por_id: UUID) -> Cheque:
        """Crea un nuevo cheque"""
        # Validar que si es de cliente, tenga empresa_id
        if data.origen == OrigenChequeEnum.RECIBIDO_CLIENTE.value and not data.empresa_id:
            raise ValueError("Para cheques recibidos de cliente, debe especificar el cliente (empresa_id)")

        cheque = Cheque(
            numero=data.numero,
            tipo=data.tipo,
            origen=data.origen,
            estado=EstadoChequeEnum.EN_CARTERA.value,
            monto=data.monto,
            fecha_emision=data.fecha_emision,
            fecha_vencimiento=data.fecha_vencimiento,
            banco_origen=data.banco_origen,
            cuenta_destino_id=data.cuenta_destino_id,
            banco_destino=data.banco_destino,
            empresa_id=data.empresa_id,
            librador=data.librador,
            cuit_librador=data.cuit_librador,
            notas=data.notas,
            registrado_por_id=registrado_por_id,
            fecha_registro=get_argentina_now()
        )

        self.db.add(cheque)
        self.db.flush()

        # Si es de cliente, imputar automáticamente en cuenta corriente
        if data.origen == OrigenChequeEnum.RECIBIDO_CLIENTE.value and data.empresa_id:
            self._imputar_cheque_cliente(
                cheque=cheque,
                empresa_id=data.empresa_id,
                usuario_id=registrado_por_id,
                es_pago=True
            )

        self.db.commit()
        self.db.refresh(cheque)
        return cheque

    def update_cheque(self, cheque_id: UUID, data: ChequeUpdate) -> Optional[Cheque]:
        """Actualiza un cheque"""
        cheque = self.get_cheque(cheque_id)
        if not cheque:
            return None

        # Solo se puede editar si está en cartera
        if cheque.estado != EstadoChequeEnum.EN_CARTERA.value:
            raise ValueError("Solo se pueden editar cheques en cartera")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cheque, field, value)

        self.db.commit()
        self.db.refresh(cheque)
        return cheque

    def depositar_cheque(
        self,
        cheque_id: UUID,
        data: DepositarChequeRequest,
        usuario_id: UUID
    ) -> Cheque:
        """Deposita un cheque en una cuenta bancaria"""
        cheque = self.get_cheque(cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        if cheque.estado != EstadoChequeEnum.EN_CARTERA.value:
            raise ValueError("Solo se pueden depositar cheques en cartera")

        # Actualizar cheque
        cheque.estado = EstadoChequeEnum.DEPOSITADO.value
        cheque.cuenta_destino_id = data.cuenta_destino_id
        cheque.fecha_deposito = data.fecha_deposito or date.today()
        if data.notas:
            cheque.notas = (cheque.notas or "") + f"\nDepósito: {data.notas}"

        self.db.commit()
        self.db.refresh(cheque)
        return cheque

    def cobrar_cheque(
        self,
        cheque_id: UUID,
        data: CobrarChequeRequest,
        usuario_id: UUID
    ) -> Cheque:
        """Confirma el cobro de un cheque"""
        cheque = self.get_cheque(cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        if cheque.estado not in [EstadoChequeEnum.EN_CARTERA.value, EstadoChequeEnum.DEPOSITADO.value]:
            raise ValueError("Solo se pueden cobrar cheques en cartera o depositados")

        # Actualizar cheque
        cheque.estado = EstadoChequeEnum.COBRADO.value
        cheque.fecha_cobro = data.fecha_cobro or date.today()
        cheque.cobrado_por_id = usuario_id
        if data.notas:
            cheque.notas = (cheque.notas or "") + f"\nCobro: {data.notas}"

        # Si está vinculado a cuenta bancaria, crear movimiento bancario
        if cheque.cuenta_destino_id:
            self._crear_movimiento_bancario_cheque(cheque, usuario_id)

        self.db.commit()
        self.db.refresh(cheque)
        return cheque

    def rechazar_cheque(
        self,
        cheque_id: UUID,
        data: RechazarChequeRequest,
        usuario_id: UUID
    ) -> Cheque:
        """Rechaza un cheque y revierte el pago si es de cliente"""
        cheque = self.get_cheque(cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        # Guardar estado anterior para la reversión
        estado_anterior = cheque.estado

        # Actualizar cheque
        cheque.estado = EstadoChequeEnum.RECHAZADO.value
        cheque.motivo_rechazo = data.motivo_rechazo

        # Si era de cliente, REVERTIR el pago (sumar deuda nuevamente)
        if cheque.origen == OrigenChequeEnum.RECIBIDO_CLIENTE.value and cheque.empresa_id:
            self._imputar_cheque_cliente(
                cheque=cheque,
                empresa_id=cheque.empresa_id,
                usuario_id=usuario_id,
                es_pago=False,  # NO es pago, es cargo (reversión)
                motivo=f"Cheque rechazado: {data.motivo_rechazo}"
            )

        self.db.commit()
        self.db.refresh(cheque)
        return cheque

    def entregar_cheque(
        self,
        cheque_id: UUID,
        data: EntregarChequeRequest,
        usuario_id: UUID
    ) -> Cheque:
        """Entrega un cheque a un tercero como forma de pago"""
        cheque = self.get_cheque(cheque_id)
        if not cheque:
            raise ValueError("Cheque no encontrado")

        if cheque.estado != EstadoChequeEnum.EN_CARTERA.value:
            raise ValueError("Solo se pueden entregar cheques en cartera")

        # Actualizar cheque
        cheque.estado = EstadoChequeEnum.ENTREGADO.value
        cheque.fecha_entrega = data.fecha_entrega or date.today()
        cheque.concepto_entrega = data.concepto
        if data.notas:
            cheque.notas = (cheque.notas or "") + f"\nEntrega: {data.notas}"

        self.db.commit()
        self.db.refresh(cheque)
        return cheque

    def delete_cheque(self, cheque_id: UUID) -> bool:
        """Elimina (soft delete) un cheque"""
        cheque = self.get_cheque(cheque_id)
        if not cheque:
            return False

        if cheque.estado != EstadoChequeEnum.EN_CARTERA.value:
            raise ValueError("Solo se pueden eliminar cheques en cartera")

        cheque.activo = False
        cheque.estado = EstadoChequeEnum.ANULADO.value

        # Si era de cliente, revertir el pago
        if cheque.origen == OrigenChequeEnum.RECIBIDO_CLIENTE.value and cheque.empresa_id:
            self._imputar_cheque_cliente(
                cheque=cheque,
                empresa_id=cheque.empresa_id,
                usuario_id=cheque.registrado_por_id,
                es_pago=False,
                motivo="Cheque anulado"
            )

        self.db.commit()
        return True

    def _imputar_cheque_cliente(
        self,
        cheque: Cheque,
        empresa_id: UUID,
        usuario_id: UUID,
        es_pago: bool,
        motivo: Optional[str] = None
    ) -> MovimientoCuentaCorriente:
        """Imputa un cheque en la cuenta corriente del cliente"""
        empresa = self.db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise ValueError("Cliente no encontrado")

        # Obtener saldo anterior
        saldo_anterior = self._get_saldo_cuenta_corriente(empresa_id)

        if es_pago:
            tipo = "pago"
            descripcion = f"Pago con cheque #{cheque.numero}"
            saldo_posterior = saldo_anterior - cheque.monto
        else:
            tipo = "cargo"
            descripcion = motivo or f"Reversión cheque #{cheque.numero}"
            saldo_posterior = saldo_anterior + cheque.monto

        movimiento = MovimientoCuentaCorriente(
            empresa_id=empresa_id,
            tipo=tipo,
            monto=cheque.monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            fecha=date.today(),
            descripcion=descripcion,
            metodo_pago="cheque",
            referencia_pago=f"CH-{cheque.numero}",
            banco=cheque.banco_origen,
            created_by=usuario_id
        )

        self.db.add(movimiento)
        self.db.flush()

        # Si es pago, generar recibo
        if es_pago:
            self._generar_recibo(
                empresa_id=empresa_id,
                monto=cheque.monto,
                concepto=f"Pago con cheque #{cheque.numero}",
                metodo_pago="cheque",
                cheque_id=cheque.id,
                usuario_id=usuario_id
            )

        return movimiento

    def _get_saldo_cuenta_corriente(self, empresa_id: UUID) -> Decimal:
        """Obtiene el saldo actual de cuenta corriente de un cliente"""
        ultimo_movimiento = self.db.query(MovimientoCuentaCorriente).filter(
            MovimientoCuentaCorriente.empresa_id == empresa_id,
            MovimientoCuentaCorriente.anulado == False
        ).order_by(MovimientoCuentaCorriente.created_at.desc()).first()

        if ultimo_movimiento:
            return ultimo_movimiento.saldo_posterior
        return Decimal("0")

    def _crear_movimiento_bancario_cheque(self, cheque: Cheque, usuario_id: UUID):
        """Crea movimiento bancario cuando se cobra un cheque"""
        cuenta = self.db.query(CuentaBancaria).filter(
            CuentaBancaria.id == cheque.cuenta_destino_id
        ).first()

        if not cuenta:
            return

        saldo_anterior = cuenta.saldo_actual
        saldo_posterior = saldo_anterior + cheque.monto

        movimiento = MovimientoBancario(
            cuenta_id=cheque.cuenta_destino_id,
            tipo="ingreso",
            concepto=f"Cobro cheque #{cheque.numero}",
            monto=cheque.monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            fecha=cheque.fecha_cobro or date.today(),
            cheque_id=cheque.id,
            empresa_id=cheque.empresa_id,
            registrado_por_id=usuario_id
        )

        self.db.add(movimiento)

        # Actualizar saldo de la cuenta
        cuenta.saldo_actual = saldo_posterior

    def _enrich_cheque(self, cheque: Cheque) -> Dict[str, Any]:
        """Enriquece datos del cheque con información relacionada"""
        data = {
            "id": cheque.id,
            "numero": cheque.numero,
            "tipo": cheque.tipo,
            "origen": cheque.origen,
            "estado": cheque.estado,
            "monto": cheque.monto,
            "fecha_emision": cheque.fecha_emision,
            "fecha_vencimiento": cheque.fecha_vencimiento,
            "fecha_cobro": cheque.fecha_cobro,
            "fecha_deposito": cheque.fecha_deposito,
            "fecha_entrega": cheque.fecha_entrega,
            "banco_origen": cheque.banco_origen,
            "banco_destino": cheque.banco_destino,
            "librador": cheque.librador,
            "cuit_librador": cheque.cuit_librador,
            "notas": cheque.notas,
            "motivo_rechazo": cheque.motivo_rechazo,
            "concepto_entrega": cheque.concepto_entrega,
            "empresa_id": cheque.empresa_id,
            "cuenta_destino_id": cheque.cuenta_destino_id,
            "registrado_por_id": cheque.registrado_por_id,
            "cobrado_por_id": cheque.cobrado_por_id,
            "fecha_registro": cheque.fecha_registro,
            "activo": cheque.activo,
            "created_at": cheque.created_at,
            "updated_at": cheque.updated_at
        }

        # Enriquecer con nombre de empresa
        if cheque.empresa_id:
            empresa = self.db.query(Empresa).filter(Empresa.id == cheque.empresa_id).first()
            data["empresa_nombre"] = empresa.nombre if empresa else None
        else:
            data["empresa_nombre"] = None

        # Enriquecer con nombre de quien registró
        if cheque.registrado_por_id:
            usuario = self.db.query(Usuario).filter(Usuario.id == cheque.registrado_por_id).first()
            data["registrado_por_nombre"] = usuario.nombre if usuario else None
        else:
            data["registrado_por_nombre"] = None

        # Enriquecer con nombre de quien cobró
        if cheque.cobrado_por_id:
            usuario = self.db.query(Usuario).filter(Usuario.id == cheque.cobrado_por_id).first()
            data["cobrado_por_nombre"] = usuario.nombre if usuario else None
        else:
            data["cobrado_por_nombre"] = None

        # Calcular días para vencimiento
        if cheque.fecha_vencimiento:
            delta = (cheque.fecha_vencimiento - date.today()).days
            data["dias_para_vencimiento"] = delta
        else:
            data["dias_para_vencimiento"] = None

        return data

    # ==================== MOVIMIENTOS DE TESORERÍA ====================

    def get_movimientos_tesoreria(
        self,
        skip: int = 0,
        limit: int = 50,
        tipo: Optional[str] = None,
        es_ingreso: Optional[bool] = None,
        metodo_pago: Optional[str] = None,
        empresa_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        buscar: Optional[str] = None,
        incluir_anulados: bool = False
    ) -> Dict[str, Any]:
        """Obtiene lista de movimientos de tesorería"""
        query = self.db.query(MovimientoTesoreria).filter(MovimientoTesoreria.activo == True)

        if not incluir_anulados:
            query = query.filter(MovimientoTesoreria.anulado == False)

        if tipo:
            query = query.filter(MovimientoTesoreria.tipo == tipo)

        if es_ingreso is not None:
            query = query.filter(MovimientoTesoreria.es_ingreso == es_ingreso)

        if metodo_pago:
            query = query.filter(MovimientoTesoreria.metodo_pago == metodo_pago)

        if empresa_id:
            query = query.filter(MovimientoTesoreria.empresa_id == empresa_id)

        if fecha_desde:
            query = query.filter(MovimientoTesoreria.fecha_movimiento >= fecha_desde)

        if fecha_hasta:
            query = query.filter(MovimientoTesoreria.fecha_movimiento <= fecha_hasta)

        if buscar:
            query = query.filter(
                or_(
                    MovimientoTesoreria.concepto.ilike(f"%{buscar}%"),
                    MovimientoTesoreria.descripcion.ilike(f"%{buscar}%")
                )
            )

        total = query.count()

        query = query.order_by(MovimientoTesoreria.fecha_movimiento.desc(), MovimientoTesoreria.created_at.desc())
        movimientos = query.offset(skip).limit(limit).all()

        items = [self._enrich_movimiento_tesoreria(m) for m in movimientos]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    def create_movimiento_tesoreria(
        self,
        data: MovimientoTesoreriaCreate,
        registrado_por_id: UUID
    ) -> MovimientoTesoreria:
        """Crea un nuevo movimiento de tesorería"""
        movimiento = MovimientoTesoreria(
            tipo=data.tipo,
            concepto=data.concepto,
            descripcion=data.descripcion,
            monto=data.monto,
            es_ingreso=data.es_ingreso,
            fecha_movimiento=data.fecha_movimiento,
            fecha_valor=data.fecha_valor,
            metodo_pago=data.metodo_pago,
            banco_origen=data.banco_origen,
            banco_destino=data.banco_destino,
            cuenta_destino_id=data.cuenta_destino_id,
            numero_transferencia=data.numero_transferencia,
            cheque_id=data.cheque_id,
            empresa_id=data.empresa_id,
            pesaje_id=data.pesaje_id,
            cobro_id=data.cobro_id,
            notas=data.notas,
            comprobante=data.comprobante,
            registrado_por_id=registrado_por_id
        )

        self.db.add(movimiento)

        # Si tiene cuenta destino y es transferencia, crear movimiento bancario
        if data.cuenta_destino_id and data.metodo_pago == MetodoPagoEnum.TRANSFERENCIA.value:
            self._crear_movimiento_bancario_transferencia(movimiento, registrado_por_id)

        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def anular_movimiento_tesoreria(
        self,
        movimiento_id: UUID,
        data: AnularMovimientoRequest,
        usuario_id: UUID
    ) -> MovimientoTesoreria:
        """Anula un movimiento de tesorería"""
        movimiento = self.db.query(MovimientoTesoreria).filter(
            MovimientoTesoreria.id == movimiento_id,
            MovimientoTesoreria.activo == True
        ).first()

        if not movimiento:
            raise ValueError("Movimiento no encontrado")

        if movimiento.anulado:
            raise ValueError("El movimiento ya está anulado")

        movimiento.anulado = True
        movimiento.motivo_anulacion = data.motivo
        movimiento.anulado_por_id = usuario_id
        movimiento.fecha_anulacion = get_argentina_now()

        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def _crear_movimiento_bancario_transferencia(
        self,
        movimiento: MovimientoTesoreria,
        usuario_id: UUID
    ):
        """Crea movimiento bancario para una transferencia"""
        cuenta = self.db.query(CuentaBancaria).filter(
            CuentaBancaria.id == movimiento.cuenta_destino_id
        ).first()

        if not cuenta:
            return

        saldo_anterior = cuenta.saldo_actual
        if movimiento.es_ingreso:
            saldo_posterior = saldo_anterior + movimiento.monto
        else:
            saldo_posterior = saldo_anterior - movimiento.monto

        mov_bancario = MovimientoBancario(
            cuenta_id=movimiento.cuenta_destino_id,
            tipo="ingreso" if movimiento.es_ingreso else "egreso",
            concepto=movimiento.concepto,
            descripcion=movimiento.descripcion,
            monto=movimiento.monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            fecha=movimiento.fecha_movimiento,
            fecha_valor=movimiento.fecha_valor,
            numero_operacion=movimiento.numero_transferencia,
            movimiento_tesoreria_id=movimiento.id,
            empresa_id=movimiento.empresa_id,
            registrado_por_id=usuario_id
        )

        self.db.add(mov_bancario)
        cuenta.saldo_actual = saldo_posterior

    def _enrich_movimiento_tesoreria(self, mov: MovimientoTesoreria) -> Dict[str, Any]:
        """Enriquece datos del movimiento"""
        data = {
            "id": mov.id,
            "tipo": mov.tipo,
            "concepto": mov.concepto,
            "descripcion": mov.descripcion,
            "monto": mov.monto,
            "es_ingreso": mov.es_ingreso,
            "fecha_movimiento": mov.fecha_movimiento,
            "fecha_valor": mov.fecha_valor,
            "metodo_pago": mov.metodo_pago,
            "banco_origen": mov.banco_origen,
            "banco_destino": mov.banco_destino,
            "numero_transferencia": mov.numero_transferencia,
            "empresa_id": mov.empresa_id,
            "pesaje_id": mov.pesaje_id,
            "cobro_id": mov.cobro_id,
            "cheque_id": mov.cheque_id,
            "cuenta_destino_id": mov.cuenta_destino_id,
            "notas": mov.notas,
            "comprobante": mov.comprobante,
            "registrado_por_id": mov.registrado_por_id,
            "anulado": mov.anulado,
            "motivo_anulacion": mov.motivo_anulacion,
            "anulado_por_id": mov.anulado_por_id,
            "fecha_anulacion": mov.fecha_anulacion,
            "activo": mov.activo,
            "created_at": mov.created_at,
            "updated_at": mov.updated_at
        }

        # Enriquecer con nombre de empresa
        if mov.empresa_id:
            empresa = self.db.query(Empresa).filter(Empresa.id == mov.empresa_id).first()
            data["empresa_nombre"] = empresa.nombre if empresa else None
        else:
            data["empresa_nombre"] = None

        # Enriquecer con nombre de quien registró
        if mov.registrado_por_id:
            usuario = self.db.query(Usuario).filter(Usuario.id == mov.registrado_por_id).first()
            data["registrado_por_nombre"] = usuario.nombre if usuario else None
        else:
            data["registrado_por_nombre"] = None

        # Enriquecer con número de cheque
        if mov.cheque_id:
            cheque = self.db.query(Cheque).filter(Cheque.id == mov.cheque_id).first()
            data["cheque_numero"] = cheque.numero if cheque else None
        else:
            data["cheque_numero"] = None

        # Enriquecer con número de pesaje
        if mov.pesaje_id:
            pesaje = self.db.query(Pesaje).filter(Pesaje.id == mov.pesaje_id).first()
            data["pesaje_numero"] = pesaje.numero_pesaje if pesaje else None
        else:
            data["pesaje_numero"] = None

        return data

    # ==================== CAJAS DE EFECTIVO ====================

    def get_cajas(self, solo_activas: bool = True) -> List[CajaEfectivo]:
        """Obtiene todas las cajas de efectivo"""
        query = self.db.query(CajaEfectivo)
        if solo_activas:
            query = query.filter(CajaEfectivo.activo == True)
        return query.order_by(CajaEfectivo.es_principal.desc(), CajaEfectivo.nombre).all()

    def get_caja(self, caja_id: UUID) -> Optional[CajaEfectivo]:
        """Obtiene una caja por ID"""
        return self.db.query(CajaEfectivo).filter(CajaEfectivo.id == caja_id).first()

    def create_caja(self, data: CajaEfectivoCreate) -> CajaEfectivo:
        """Crea una nueva caja de efectivo"""
        caja = CajaEfectivo(
            nombre=data.nombre,
            descripcion=data.descripcion,
            saldo_inicial=data.saldo_inicial,
            saldo_actual=data.saldo_inicial,
            moneda=data.moneda,
            es_principal=data.es_principal,
            notas=data.notas
        )

        # Si es principal, quitar el flag de las demás
        if data.es_principal:
            self.db.query(CajaEfectivo).update({CajaEfectivo.es_principal: False})

        self.db.add(caja)
        self.db.commit()
        self.db.refresh(caja)
        return caja

    def update_caja(self, caja_id: UUID, data: CajaEfectivoUpdate) -> Optional[CajaEfectivo]:
        """Actualiza una caja de efectivo"""
        caja = self.get_caja(caja_id)
        if not caja:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Si se marca como principal, quitar flag de las demás
        if update_data.get("es_principal"):
            self.db.query(CajaEfectivo).filter(
                CajaEfectivo.id != caja_id
            ).update({CajaEfectivo.es_principal: False})

        for field, value in update_data.items():
            setattr(caja, field, value)

        self.db.commit()
        self.db.refresh(caja)
        return caja

    def create_movimiento_caja(
        self,
        data: MovimientoCajaCreate,
        registrado_por_id: UUID
    ) -> MovimientoCaja:
        """Crea un movimiento en una caja de efectivo"""
        caja = self.get_caja(data.caja_id)
        if not caja:
            raise ValueError("Caja no encontrada")

        saldo_anterior = caja.saldo_actual
        if data.tipo == "ingreso":
            saldo_posterior = saldo_anterior + data.monto
        else:
            saldo_posterior = saldo_anterior - data.monto
            if saldo_posterior < 0:
                raise ValueError("Saldo insuficiente en caja")

        movimiento = MovimientoCaja(
            caja_id=data.caja_id,
            tipo=data.tipo,
            concepto=data.concepto,
            descripcion=data.descripcion,
            monto=data.monto,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            fecha=data.fecha,
            empresa_id=data.empresa_id,
            notas=data.notas,
            registrado_por_id=registrado_por_id
        )

        self.db.add(movimiento)

        # Actualizar saldo de la caja
        caja.saldo_actual = saldo_posterior

        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def get_movimientos_caja(
        self,
        caja_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Obtiene movimientos de caja"""
        query = self.db.query(MovimientoCaja).filter(MovimientoCaja.anulado == False)

        if caja_id:
            query = query.filter(MovimientoCaja.caja_id == caja_id)

        if fecha_desde:
            query = query.filter(MovimientoCaja.fecha >= fecha_desde)

        if fecha_hasta:
            query = query.filter(MovimientoCaja.fecha <= fecha_hasta)

        total = query.count()

        query = query.order_by(MovimientoCaja.fecha.desc(), MovimientoCaja.created_at.desc())
        movimientos = query.offset(skip).limit(limit).all()

        return {
            "items": movimientos,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    # ==================== CUENTAS BANCARIAS ====================

    def get_cuentas_bancarias(self, solo_activas: bool = True) -> List[CuentaBancaria]:
        """Obtiene todas las cuentas bancarias"""
        query = self.db.query(CuentaBancaria)
        if solo_activas:
            query = query.filter(CuentaBancaria.activo == True)
        return query.order_by(CuentaBancaria.banco, CuentaBancaria.nombre).all()

    def get_cuenta_bancaria(self, cuenta_id: UUID) -> Optional[CuentaBancaria]:
        """Obtiene una cuenta bancaria por ID"""
        return self.db.query(CuentaBancaria).filter(CuentaBancaria.id == cuenta_id).first()

    def create_cuenta_bancaria(self, data: CuentaBancariaCreate) -> CuentaBancaria:
        """Crea una nueva cuenta bancaria"""
        cuenta = CuentaBancaria(
            nombre=data.nombre,
            banco=data.banco,
            tipo_cuenta=data.tipo_cuenta,
            numero_cuenta=data.numero_cuenta,
            cbu=data.cbu,
            alias=data.alias,
            titular=data.titular,
            cuit_titular=data.cuit_titular,
            saldo_inicial=data.saldo_inicial,
            saldo_actual=data.saldo_inicial,
            moneda=data.moneda,
            notas=data.notas
        )

        self.db.add(cuenta)
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def update_cuenta_bancaria(self, cuenta_id: UUID, data: CuentaBancariaUpdate) -> Optional[CuentaBancaria]:
        """Actualiza una cuenta bancaria"""
        cuenta = self.get_cuenta_bancaria(cuenta_id)
        if not cuenta:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cuenta, field, value)

        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def get_movimientos_bancarios(
        self,
        cuenta_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Obtiene movimientos bancarios"""
        query = self.db.query(MovimientoBancario).filter(MovimientoBancario.anulado == False)

        if cuenta_id:
            query = query.filter(MovimientoBancario.cuenta_id == cuenta_id)

        if fecha_desde:
            query = query.filter(MovimientoBancario.fecha >= fecha_desde)

        if fecha_hasta:
            query = query.filter(MovimientoBancario.fecha <= fecha_hasta)

        total = query.count()

        query = query.order_by(MovimientoBancario.fecha.desc(), MovimientoBancario.created_at.desc())
        movimientos = query.offset(skip).limit(limit).all()

        return {
            "items": movimientos,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    # ==================== GASTOS ====================

    def get_gastos(
        self,
        skip: int = 0,
        limit: int = 50,
        categoria: Optional[str] = None,
        metodo_pago: Optional[str] = None,
        empresa_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        buscar: Optional[str] = None,
        incluir_anulados: bool = False
    ) -> Dict[str, Any]:
        """Obtiene lista de gastos"""
        query = self.db.query(Gasto).filter(Gasto.activo == True)

        if not incluir_anulados:
            query = query.filter(Gasto.anulado == False)

        if categoria:
            query = query.filter(Gasto.categoria == categoria)

        if metodo_pago:
            query = query.filter(Gasto.metodo_pago == metodo_pago)

        if empresa_id:
            query = query.filter(Gasto.empresa_id == empresa_id)

        if fecha_desde:
            query = query.filter(Gasto.fecha >= fecha_desde)

        if fecha_hasta:
            query = query.filter(Gasto.fecha <= fecha_hasta)

        if buscar:
            query = query.filter(
                or_(
                    Gasto.concepto.ilike(f"%{buscar}%"),
                    Gasto.descripcion.ilike(f"%{buscar}%"),
                    Gasto.proveedor_nombre.ilike(f"%{buscar}%")
                )
            )

        total = query.count()

        query = query.order_by(Gasto.fecha.desc(), Gasto.created_at.desc())
        gastos = query.offset(skip).limit(limit).all()

        items = [self._enrich_gasto(g) for g in gastos]

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    def get_gasto(self, gasto_id: UUID) -> Optional[Gasto]:
        """Obtiene un gasto por ID"""
        return self.db.query(Gasto).filter(
            Gasto.id == gasto_id,
            Gasto.activo == True
        ).first()

    def create_gasto(self, data: GastoCreate, registrado_por_id: UUID) -> Gasto:
        """Crea un nuevo gasto"""
        gasto = Gasto(
            fecha=data.fecha,
            concepto=data.concepto,
            descripcion=data.descripcion,
            categoria=data.categoria,
            monto=data.monto,
            empresa_id=data.empresa_id,
            proveedor_nombre=data.proveedor_nombre,
            tipo_comprobante=data.tipo_comprobante,
            numero_comprobante=data.numero_comprobante,
            comprobante_url=data.comprobante_url,
            metodo_pago=data.metodo_pago,
            cuenta_bancaria_id=data.cuenta_bancaria_id,
            caja_id=data.caja_id,
            cheque_id=data.cheque_id,
            camion_id=data.camion_id,
            servicio_id=data.servicio_id,
            notas=data.notas,
            registrado_por_id=registrado_por_id
        )

        self.db.add(gasto)
        self.db.flush()

        # Crear movimiento de tesorería asociado
        mov_tesoreria = MovimientoTesoreria(
            tipo=f"egreso_{data.metodo_pago}",
            concepto=data.concepto,
            descripcion=data.descripcion,
            monto=data.monto,
            es_ingreso=False,
            fecha_movimiento=data.fecha,
            metodo_pago=data.metodo_pago,
            cuenta_destino_id=data.cuenta_bancaria_id,
            cheque_id=data.cheque_id,
            empresa_id=data.empresa_id,
            registrado_por_id=registrado_por_id
        )

        self.db.add(mov_tesoreria)
        self.db.flush()

        gasto.movimiento_tesoreria_id = mov_tesoreria.id

        # Si es efectivo y tiene caja, crear movimiento de caja
        if data.metodo_pago == MetodoPagoEnum.EFECTIVO.value and data.caja_id:
            caja = self.get_caja(data.caja_id)
            if caja:
                saldo_anterior = caja.saldo_actual
                saldo_posterior = saldo_anterior - data.monto
                if saldo_posterior < 0:
                    raise ValueError("Saldo insuficiente en caja")

                mov_caja = MovimientoCaja(
                    caja_id=data.caja_id,
                    tipo="egreso",
                    concepto=data.concepto,
                    descripcion=data.descripcion,
                    monto=data.monto,
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_posterior,
                    fecha=data.fecha,
                    movimiento_tesoreria_id=mov_tesoreria.id,
                    empresa_id=data.empresa_id,
                    registrado_por_id=registrado_por_id
                )
                self.db.add(mov_caja)
                caja.saldo_actual = saldo_posterior

        # Si es transferencia y tiene cuenta, crear movimiento bancario
        elif data.metodo_pago == MetodoPagoEnum.TRANSFERENCIA.value and data.cuenta_bancaria_id:
            cuenta = self.get_cuenta_bancaria(data.cuenta_bancaria_id)
            if cuenta:
                saldo_anterior = cuenta.saldo_actual
                saldo_posterior = saldo_anterior - data.monto

                mov_bancario = MovimientoBancario(
                    cuenta_id=data.cuenta_bancaria_id,
                    tipo="egreso",
                    concepto=data.concepto,
                    descripcion=data.descripcion,
                    monto=data.monto,
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=saldo_posterior,
                    fecha=data.fecha,
                    movimiento_tesoreria_id=mov_tesoreria.id,
                    empresa_id=data.empresa_id,
                    registrado_por_id=registrado_por_id
                )
                self.db.add(mov_bancario)
                cuenta.saldo_actual = saldo_posterior

        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def update_gasto(self, gasto_id: UUID, data: GastoUpdate) -> Optional[Gasto]:
        """Actualiza un gasto"""
        gasto = self.get_gasto(gasto_id)
        if not gasto:
            return None

        if gasto.anulado:
            raise ValueError("No se puede editar un gasto anulado")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(gasto, field, value)

        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def anular_gasto(self, gasto_id: UUID, motivo: str, usuario_id: UUID) -> Gasto:
        """Anula un gasto"""
        gasto = self.get_gasto(gasto_id)
        if not gasto:
            raise ValueError("Gasto no encontrado")

        if gasto.anulado:
            raise ValueError("El gasto ya está anulado")

        gasto.anulado = True
        gasto.estado = "anulado"

        # Anular movimiento de tesorería asociado
        if gasto.movimiento_tesoreria_id:
            mov = self.db.query(MovimientoTesoreria).filter(
                MovimientoTesoreria.id == gasto.movimiento_tesoreria_id
            ).first()
            if mov:
                mov.anulado = True
                mov.motivo_anulacion = motivo
                mov.anulado_por_id = usuario_id
                mov.fecha_anulacion = get_argentina_now()

        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def _enrich_gasto(self, gasto: Gasto) -> Dict[str, Any]:
        """Enriquece datos del gasto"""
        data = {
            "id": gasto.id,
            "fecha": gasto.fecha,
            "concepto": gasto.concepto,
            "descripcion": gasto.descripcion,
            "categoria": gasto.categoria,
            "monto": gasto.monto,
            "empresa_id": gasto.empresa_id,
            "proveedor_nombre": gasto.proveedor_nombre,
            "tipo_comprobante": gasto.tipo_comprobante,
            "numero_comprobante": gasto.numero_comprobante,
            "comprobante_url": gasto.comprobante_url,
            "metodo_pago": gasto.metodo_pago,
            "cuenta_bancaria_id": gasto.cuenta_bancaria_id,
            "caja_id": gasto.caja_id,
            "cheque_id": gasto.cheque_id,
            "camion_id": gasto.camion_id,
            "servicio_id": gasto.servicio_id,
            "movimiento_tesoreria_id": gasto.movimiento_tesoreria_id,
            "registrado_por_id": gasto.registrado_por_id,
            "notas": gasto.notas,
            "estado": gasto.estado,
            "anulado": gasto.anulado,
            "activo": gasto.activo,
            "created_at": gasto.created_at,
            "updated_at": gasto.updated_at
        }

        # Enriquecer con nombre de empresa
        if gasto.empresa_id:
            empresa = self.db.query(Empresa).filter(Empresa.id == gasto.empresa_id).first()
            data["empresa_nombre"] = empresa.nombre if empresa else None
        else:
            data["empresa_nombre"] = None

        return data

    # ==================== RECIBOS ====================

    def _generar_recibo(
        self,
        empresa_id: UUID,
        monto: Decimal,
        concepto: str,
        metodo_pago: str,
        cheque_id: Optional[UUID] = None,
        movimiento_tesoreria_id: Optional[UUID] = None,
        cobro_id: Optional[UUID] = None,
        usuario_id: Optional[UUID] = None
    ) -> Recibo:
        """Genera un recibo automáticamente"""
        # Generar número de recibo
        hoy = date.today()
        prefijo = f"REC-{hoy.strftime('%y%m%d')}"

        # Buscar último recibo del día
        ultimo = self.db.query(Recibo).filter(
            Recibo.numero_recibo.like(f"{prefijo}%")
        ).order_by(Recibo.numero_recibo.desc()).first()

        if ultimo:
            ultimo_num = int(ultimo.numero_recibo.split("-")[-1])
            numero = f"{prefijo}-{ultimo_num + 1:04d}"
        else:
            numero = f"{prefijo}-0001"

        recibo = Recibo(
            numero_recibo=numero,
            fecha=hoy,
            empresa_id=empresa_id,
            monto=monto,
            concepto=concepto,
            metodo_pago=metodo_pago,
            cheque_id=cheque_id,
            movimiento_tesoreria_id=movimiento_tesoreria_id,
            cobro_id=cobro_id,
            registrado_por_id=usuario_id
        )

        self.db.add(recibo)
        return recibo

    def get_recibos(
        self,
        empresa_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Obtiene lista de recibos"""
        query = self.db.query(Recibo).filter(Recibo.activo == True, Recibo.anulado == False)

        if empresa_id:
            query = query.filter(Recibo.empresa_id == empresa_id)

        if fecha_desde:
            query = query.filter(Recibo.fecha >= fecha_desde)

        if fecha_hasta:
            query = query.filter(Recibo.fecha <= fecha_hasta)

        total = query.count()

        query = query.order_by(Recibo.fecha.desc(), Recibo.numero_recibo.desc())
        recibos = query.offset(skip).limit(limit).all()

        return {
            "items": recibos,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    # ==================== RESUMEN ====================

    def get_resumen(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> ResumenTesoreria:
        """Obtiene resumen de tesorería"""
        if not fecha_desde:
            fecha_desde = date.today().replace(day=1)
        if not fecha_hasta:
            fecha_hasta = date.today()

        resumen = ResumenTesoreria()

        # Cheques en cartera
        cheques_cartera = self.db.query(Cheque).filter(
            Cheque.activo == True,
            Cheque.estado == EstadoChequeEnum.EN_CARTERA.value
        ).all()

        resumen.cheques_en_cartera = len(cheques_cartera)
        resumen.total_cheques_cartera = sum(c.monto for c in cheques_cartera)

        # Cheques próximos a vencer (7 días)
        fecha_limite = date.today() + timedelta(days=7)
        cheques_proximos = [
            c for c in cheques_cartera
            if c.fecha_vencimiento and c.fecha_vencimiento <= fecha_limite and c.fecha_vencimiento >= date.today()
        ]
        resumen.cheques_proximos_vencer = len(cheques_proximos)
        resumen.total_proximos_vencer = sum(c.monto for c in cheques_proximos)

        # Cheques vencidos
        cheques_vencidos = [
            c for c in cheques_cartera
            if c.fecha_vencimiento and c.fecha_vencimiento < date.today()
        ]
        resumen.cheques_vencidos = len(cheques_vencidos)
        resumen.total_vencidos = sum(c.monto for c in cheques_vencidos)

        # Movimientos del período
        movimientos = self.db.query(MovimientoTesoreria).filter(
            MovimientoTesoreria.activo == True,
            MovimientoTesoreria.anulado == False,
            MovimientoTesoreria.fecha_movimiento >= fecha_desde,
            MovimientoTesoreria.fecha_movimiento <= fecha_hasta
        ).all()

        for mov in movimientos:
            if mov.es_ingreso:
                if mov.metodo_pago == MetodoPagoEnum.EFECTIVO.value:
                    resumen.total_ingresos_efectivo += mov.monto
                elif mov.metodo_pago == MetodoPagoEnum.TRANSFERENCIA.value:
                    resumen.total_ingresos_transferencia += mov.monto
                elif mov.metodo_pago == MetodoPagoEnum.CHEQUE.value:
                    resumen.total_ingresos_cheque += mov.monto
            else:
                if mov.metodo_pago == MetodoPagoEnum.EFECTIVO.value:
                    resumen.total_egresos_efectivo += mov.monto
                elif mov.metodo_pago == MetodoPagoEnum.TRANSFERENCIA.value:
                    resumen.total_egresos_transferencia += mov.monto
                elif mov.metodo_pago == MetodoPagoEnum.CHEQUE.value:
                    resumen.total_egresos_cheque += mov.monto

        resumen.total_ingresos = (
            resumen.total_ingresos_efectivo +
            resumen.total_ingresos_transferencia +
            resumen.total_ingresos_cheque
        )
        resumen.total_egresos = (
            resumen.total_egresos_efectivo +
            resumen.total_egresos_transferencia +
            resumen.total_egresos_cheque
        )
        resumen.saldo_periodo = resumen.total_ingresos - resumen.total_egresos

        # Saldo de cajas
        cajas = self.db.query(CajaEfectivo).filter(CajaEfectivo.activo == True).all()
        resumen.saldo_cajas = sum(c.saldo_actual for c in cajas)

        # Saldo de bancos
        cuentas = self.db.query(CuentaBancaria).filter(CuentaBancaria.activo == True).all()
        resumen.saldo_bancos = sum(c.saldo_actual for c in cuentas)

        # Total disponible
        resumen.total_disponible = resumen.saldo_cajas + resumen.saldo_bancos + resumen.total_cheques_cartera

        return resumen

    # ==================== MOVIMIENTOS CONSOLIDADOS ====================

    def get_movimientos_consolidados(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo: Optional[str] = None,
        es_ingreso: Optional[bool] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        buscar: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene movimientos consolidados de todas las fuentes"""
        movimientos = []

        # Obtener cheques
        cheques_query = self.db.query(Cheque).filter(Cheque.activo == True)

        if fecha_desde:
            cheques_query = cheques_query.filter(
                or_(
                    Cheque.fecha_cobro >= fecha_desde,
                    Cheque.created_at >= datetime.combine(fecha_desde, datetime.min.time())
                )
            )
        if fecha_hasta:
            cheques_query = cheques_query.filter(
                or_(
                    Cheque.fecha_cobro <= fecha_hasta,
                    Cheque.created_at <= datetime.combine(fecha_hasta, datetime.max.time())
                )
            )

        for cheque in cheques_query.all():
            if cheque.origen == OrigenChequeEnum.RECIBIDO_CLIENTE.value:
                es_ing = True
                tipo_mov = "cheque_recibido"
            elif cheque.origen == OrigenChequeEnum.EMITIDO.value:
                es_ing = False
                tipo_mov = "cheque_emitido"
            else:
                es_ing = True
                tipo_mov = "cheque_recibido"

            # Filtrar por tipo si se especifica
            if tipo and tipo != tipo_mov:
                continue
            if es_ingreso is not None and es_ingreso != es_ing:
                continue

            empresa_nombre = None
            if cheque.empresa_id:
                empresa = self.db.query(Empresa).filter(Empresa.id == cheque.empresa_id).first()
                empresa_nombre = empresa.nombre if empresa else None

            movimientos.append({
                "id": str(cheque.id),
                "fecha": cheque.fecha_cobro or cheque.created_at.date(),
                "tipo": tipo_mov,
                "origen": "cheque",
                "concepto": f"Cheque #{cheque.numero}" + (f" - {cheque.librador}" if cheque.librador else ""),
                "monto": cheque.monto,
                "es_ingreso": es_ing,
                "metodo_pago": "cheque",
                "empresa_nombre": empresa_nombre,
                "numero_referencia": cheque.numero,
                "banco": cheque.banco_origen,
                "estado": cheque.estado,
                "created_at": cheque.created_at
            })

        # Obtener movimientos de tesorería
        mov_query = self.db.query(MovimientoTesoreria).filter(
            MovimientoTesoreria.activo == True,
            MovimientoTesoreria.anulado == False
        )

        if fecha_desde:
            mov_query = mov_query.filter(MovimientoTesoreria.fecha_movimiento >= fecha_desde)
        if fecha_hasta:
            mov_query = mov_query.filter(MovimientoTesoreria.fecha_movimiento <= fecha_hasta)

        for mov in mov_query.all():
            # Evitar duplicados con cheques (si el movimiento es de cheque)
            if mov.cheque_id:
                continue

            if tipo and tipo != mov.tipo:
                continue
            if es_ingreso is not None and es_ingreso != mov.es_ingreso:
                continue

            empresa_nombre = None
            if mov.empresa_id:
                empresa = self.db.query(Empresa).filter(Empresa.id == mov.empresa_id).first()
                empresa_nombre = empresa.nombre if empresa else None

            movimientos.append({
                "id": str(mov.id),
                "fecha": mov.fecha_movimiento,
                "tipo": mov.tipo,
                "origen": "movimiento_tesoreria",
                "concepto": mov.concepto,
                "monto": mov.monto,
                "es_ingreso": mov.es_ingreso,
                "metodo_pago": mov.metodo_pago,
                "empresa_nombre": empresa_nombre,
                "numero_referencia": mov.numero_transferencia or mov.comprobante,
                "banco": mov.banco_destino or mov.banco_origen,
                "estado": None,
                "created_at": mov.created_at
            })

        # Ordenar por fecha descendente
        movimientos.sort(key=lambda x: (x["fecha"], x["created_at"]), reverse=True)

        # Calcular totales
        total_ingresos = sum(m["monto"] for m in movimientos if m["es_ingreso"])
        total_egresos = sum(m["monto"] for m in movimientos if not m["es_ingreso"])

        # Paginar
        total = len(movimientos)
        movimientos_paginados = movimientos[skip:skip + limit]

        return {
            "items": movimientos_paginados,
            "total": total,
            "total_ingresos": total_ingresos,
            "total_egresos": total_egresos,
            "skip": skip,
            "limit": limit
        }
