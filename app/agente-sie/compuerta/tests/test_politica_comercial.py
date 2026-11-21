import pytest
from app.motor import Compuerta
from app.snapshot import construir
from test_casos_pc3 import validar_schema


@pytest.mark.parametrize('pending,status,code', [
    (False, 'RECHAZADA', 'DATOS_INCONSISTENTES'),
    (True, 'PENDIENTE', 'DEPENDENCIA_NO_DISPONIBLE'),
])
def test_policy_gate_preserves_contract_and_audit(entorno, casos, pending, status, code):
    request = casos['PC3-N01']['solicitud']
    masters, available = construir(request, entorno.odoo, entorno.repo, entorno.config, entorno.reloj())
    masters['quotations'][request['quotation_id']]['commercial_policy'] = {
        'revision': 'MYS-2026-11-13', 'blocking_code': 'CRITERIO_NO_CUMPLIDO',
        'message': 'Datos sintéticos: regla comercial no verificada.', 'pending': pending}
    engine = Compuerta(masters, entorno.config.database, comercial_disponible=available)
    try:
        result = engine.submit(request, 'VEN-DEMO-01')
    finally:
        engine.close()
    assert result['status'] == status and result['code'] == code
    validar_schema(result)
    with entorno.repo.conexion() as db:
        assert db.execute("SELECT COUNT(*) FROM audit WHERE code='POLITICA_COMERCIAL_MYS'").fetchone()[0] == 1


def test_manager_cannot_approve_without_proven_business_criterion(entorno):
    original = entorno.odoo.versiones_cotizacion
    def versions(quotation):
        return [dict(v, policy_report={'exceptional_eligible': False, 'blocking_code': 'NO_ELEGIBLE',
                                      'message': 'No hay criterio estratégico.'}) for v in original(quotation)]
    entorno.odoo.versiones_cotizacion = versions
    response = entorno.llamar('POST', '/aprobaciones', rol='GERENCIA', json={
        'quotation_id': 'COT-DEMO-004', 'version': 3, 'total': '1800.00',
        'decision': 'APROBADA', 'motivo': 'Prueba de restricción', 'correlation_id': 'COR-POLICY'})
    assert response.status_code == 409
