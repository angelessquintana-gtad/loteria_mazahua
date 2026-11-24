"""Correo transaccional por SMTP cifrado; nunca registra enlaces ni contraseñas."""
import logging
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def correo_disponible():
    url = urlsplit(os.getenv('PUBLIC_URL', ''))
    from configuracion import PRODUCCION
    origen_valido = (url.scheme == 'https' or (not PRODUCCION and url.scheme == 'http' and url.hostname in {'localhost', '127.0.0.1'}))
    proveedor = os.getenv('MAIL_PROVIDER', 'smtp')
    transporte = (bool(os.getenv('BREVO_API_KEY') and os.getenv('MAIL_FROM')) if proveedor == 'brevo' else
                  bool(proveedor == 'smtp' and os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM') and
                       os.getenv('SMTP_SECURITY', 'starttls') in {'starttls', 'ssl'}))
    return bool(origen_valido and url.netloc and not url.username and not url.password and
                url.path in {'', '/'} and not url.query and not url.fragment and transporte)


def enviar_recuperacion(destinatario, token):
    mensaje = EmailMessage()
    mensaje['Subject'] = 'Recuperar tu acceso · Lotería Mazahua'
    mensaje['From'] = os.getenv('MAIL_FROM') if os.getenv('MAIL_PROVIDER') == 'brevo' else os.environ['SMTP_FROM']
    mensaje['To'] = destinatario
    enlace = os.environ['PUBLIC_URL'].rstrip('/') + '/acceso#recuperar=' + token
    mensaje.set_content('Se solicitó cambiar tu contraseña de Lotería Mazahua.\n\n'
                        f'Abre este enlace en los próximos 30 minutos:\n{enlace}\n\n'
                        'Si no lo solicitaste, ignora este mensaje. Tu contraseña no ha cambiado.')
    try:
        if os.getenv('MAIL_PROVIDER') == 'brevo':
            datos = {'sender':{'email':os.environ['MAIL_FROM'], 'name':'Lotería Mazahua'},
                     'to':[{'email':destinatario}], 'subject':str(mensaje['Subject']), 'textContent':mensaje.get_content()}
            peticion = Request('https://api.brevo.com/v3/smtp/email', data=json.dumps(datos).encode(),
                               headers={'api-key':os.environ['BREVO_API_KEY'], 'Content-Type':'application/json'}, method='POST')
            with urlopen(peticion, timeout=15):
                return True
        seguridad = os.getenv('SMTP_SECURITY', 'starttls')
        puerto = int(os.getenv('SMTP_PORT', '465' if seguridad == 'ssl' else '587'))
        contexto = ssl.create_default_context()
        if seguridad == 'ssl':
            cliente = smtplib.SMTP_SSL(os.environ['SMTP_HOST'], puerto, timeout=15, context=contexto)
        else:
            cliente = smtplib.SMTP(os.environ['SMTP_HOST'], puerto, timeout=15)
        with cliente:
            if seguridad != 'ssl':
                cliente.starttls(context=contexto)
            if os.getenv('SMTP_USER'):
                cliente.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
            cliente.send_message(mensaje)
        return True
    except Exception:
        # No incluir la excepción: algunos servidores repiten contenido o destinatarios.
        logging.getLogger('mazahua.correo').error('No se pudo entregar un correo de recuperación. Revisar configuración SMTP y proveedor.')
        return False
