"""Completa app/.env con claves locales aleatorias sin imprimirlas ni reemplazar las existentes."""
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def leer_env(path=None):
    path = path or ROOT / '.env'
    if not path.exists():
        return {}
    return {k.strip(): v.strip() for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.lstrip().startswith('#') and '=' in line
            for k, v in [line.split('=', 1)]}


def main():
    path = ROOT / '.env'
    if not path.exists():
        path.write_text((ROOT / '.env.example').read_text(encoding='utf-8'), encoding='utf-8')
    text = path.read_text(encoding='utf-8')
    env = leer_env()
    required = {'ODOO_READER_USER': 'sie-lectura', 'ODOO_READER_PASSWORD': None,
                'ODOO_SELLER_PASSWORD': 'vendedor01', 'ODOO_OWNER_PASSWORD': 'gerente',
                'TOKEN_ODOO': None, 'TOKEN_AGENTE': None, 'ODOO_BRIDGE_SECRET': None, 'N8N_WEBHOOK_SECRET': None,
                'GEMINI_MODEL': 'models/gemini-3.5-flash-lite',
                'CORREO_DUENO': 'dueno@mys-demo.local', 'CORREO_REMITENTE': 'agente-sie@mys-demo.local',
                'SMTP_HOST': 'mailpit', 'SMTP_PORT': '1025', 'SMTP_SEGURO': 'false',
                'APP_PORT': '8088', 'COTIZACION_HORA_CIERRE': '23:59',
                'N8N_OWNER_EMAIL': 'admin@mys.local', 'N8N_OWNER_PASSWORD': None}
    for key, value in list(env.items()):
        if value.startswith('cambiar-esto') and any(x in key for x in ('PASSWORD', 'TOKEN', 'KEY', 'SECRET')):
            replacement = secrets.token_urlsafe(36)
            text = text.replace(f'{key}={value}', f'{key}={replacement}')
    for key, default in required.items():
        if key not in env:
            value = default if default is not None else ('MysA1!' + secrets.token_urlsafe(32))
            text += f'\n{key}={value}\n'
    path.write_text(text, encoding='utf-8')
    print('Configuración local preparada en app/.env. Las claves existentes se conservaron.')
    print('Ningún secreto fue impreso. Gemini es opcional; el modo determinista funciona sin clave.')


if __name__ == '__main__':
    main()
