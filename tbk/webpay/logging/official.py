

PAYMENT_FORMAT = (
    "          ;{pid:>12d}; ;Filtro    ;Inicio                                  ;{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;Inicio de filtrado\n"  # noqa
    "          ;{pid:>12d}; ;Filtro    ;tbk_param.txt                           ;{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;Archivo parseado\n"  # noqa
    "          ;{pid:>12d}; ;Filtro    ;Terminado                               ;{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;Datos Filtrados con exito\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;inicio                                  ;{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Parseo realizado\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Datos en datos/tbk_config.dat\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Mac generado\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Construccion TBK_PARAM\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};TBK_PARAM encriptado\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Datos listos para ser enviados\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Medio 1: Transaccion segura\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Datos validados\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Token={token:s}\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Redireccion web\n"  # noqa
    "{transaction_id:<10d};{pid:>12d}; ;pago      ;{webpay_server:<40s};{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Todo OK\n"  # noqa
)

CONFIRMATION_FORMAT = (
    "          ;{pid:>12d};   ;resultado ;Desencriptando                          ;%{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;TBK_PARAM desencriptado\n"  # noqa
    "          ;{pid:>12d};   ;resultado ;Validacion                              ;%{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;Entidad emisora de los datos validada\n"  # noqa
    "          ;{pid:>12d};   ;resultado ;{order_id:<40s};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;Parseo de los datos\n"  # noqa
    "          ;{pid:>12d};   ;resultado ;{order_id:<40s};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;                    ;http://127.0.0.1/webpay/notify\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;transacc  ;{transaction_id:<40d};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};conectandose al port :(80)\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;resultado ;logro abrir_conexion                    ;%{date:<14s};{time:<6s};{request_ip:<15s}; 0 ;{commerce_id:<20d};Abrio socket para conex-com\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;transacc  ;{transaction_id:<40d};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};POST a url http://127.0.0.1/webpay/notify\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;transacc  ;{transaction_id:<40d};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};mensaje enviado\n"  # noqa
    "          ;{pid:>12d};   ;check_mac ;                                        ;%{date:<14s};{time:<6s};EMPTY          ;OK ;                    ;Todo OK\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;transacc  ;{transaction_id:<40d};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Llego ACK del Comercio\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;resultado ;{order_id:<40s};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};tienda acepto transaccion\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;resultado ;{order_id:<40s};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};respuesta enviada a TBK (ACK)\n"  # noqa
    "{transaction_id:<10d};{pid:>12d};   ;resultado ;{order_id:<40s};%{date:<14s};{time:<6s};{request_ip:<15s};OK ;{commerce_id:<20d};Todo OK\n"  # noqa
)

BITACORA_FORMAT = (
    "ACK; "
    "TBK_ORDEN_COMPRA=%{TBK_ORDEN_COMPRA}s; "
    "TBK_CODIGO_COMERCIO=%{commerce_id}s; "
    "TBK_TIPO_TRANSACCION=%{TBK_TIPO_TRANSACCION}s; "
    "TBK_RESPUESTA=%{TBK_RESPUESTA}s; "
    "TBK_MONTO=%{TBK_MONTO}s; "
    "TBK_CODIGO_AUTORIZACION=%{TBK_CODIGO_AUTORIZACION}s; "
    "TBK_FINAL_NUMERO_TARJETA=%{TBK_FINAL_NUMERO_TARJETA}s; "
    "TBK_FECHA_CONTABLE=%{TBK_FECHA_CONTABLE}s; "
    "TBK_FECHA_TRANSACCION=%{TBK_FECHA_TRANSACCION}s; "
    "TBK_HORA_TRANSACCION=%{TBK_HORA_TRANSACCION}s; "
    "TBK_ID_SESION=%{TBK_ID_SESION}s; "
    "TBK_ID_TRANSACCION=%{TBK_ID_TRANSACCION}s; "
    "TBK_TIPO_PAGO=%{TBK_TIPO_PAGO}s; "
    "TBK_NUMERO_CUOTAS=%{TBK_NUMERO_CUOTAS}s; "
    "TBK_VCI=%{TBK_VCI}s; "
    "TBK_MAC=%{TBK_MAC}s\n"
)


class WebpayOfficialHandler(object):

    def __init__(self, path=None):
        self.path = path
        self.events_log_file = None
        self.bitacora_log_file = None

    def event_payment(self, **kwargs):
        self.events_log_file.write(PAYMENT_FORMAT.format(**kwargs))

    def event_confirmation(self, **kwargs):
        self.events_log_file.write(CONFIRMATION_FORMAT.format(**kwargs))

    def log_confirmation(self, params, commerce_id):
        format_params = {'commerce_id': commerce_id}
        format_params.update(**params)
        self.bitacora_log_file.write(BITACORA_FORMAT % format_params)
