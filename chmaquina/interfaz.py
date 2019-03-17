import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from chmaquina.maquina import Maquina


class TecladoGtk(object):
    def __init__(self, padre):
        self.padre = padre

    def lea(self):
        dialogo = Gtk.MessageDialog(
            self.padre,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.OK,
            "Esperando entrada",
        )

        dialogo.set_title("Entrada de teclado")

        espacio_dialogo = dialogo.get_content_area()
        entrada_de_usuario = Gtk.Entry()
        entrada_de_usuario.set_size_request(250, 0)
        espacio_dialogo.pack_end(entrada_de_usuario, False, False, 0)

        dialogo.show_all()
        response = dialogo.run()
        text = entrada_de_usuario.get_text()
        dialogo.destroy()
        if response == Gtk.ResponseType.OK:
            return text


class InterfazChMaquina:
    """
    Controlador de la interfaz gráfica del ch maquina.
    """

    def __init__(self, constructor):
        self.constructor = constructor
        self.maquina = None
        self.estado = None
        self.ventana = constructor.get_object("chmaquina")
        self.tabla_memoria = constructor.get_object("tabla-memoria")
        self.tabla_variables = constructor.get_object("tabla-variables")
        self.tabla_etiquetas = constructor.get_object("tabla-etiquetas")
        self.tabla_programas = constructor.get_object("tabla-programas")
        self.preparar_tabla(
            self.tabla_memoria, ["Posición", "Programa", "Tipo", "Nombre", "Valor"]
        )
        self.preparar_tabla(self.tabla_variables, ["Programa", "Nombre", "Posición"])
        self.preparar_tabla(self.tabla_etiquetas, ["Programa", "Nombre", "Posición"])
        self.preparar_tabla(
            self.tabla_programas,
            ["Programa", "Llegada", "Inicio", "Datos", "Fin", "Contador"],
        )
        self.preferencias = {
            "tamano_memoria": 512,
            "tamano_kernel": 79,
            "algoritmo": "FAFS",
        }
        self.redibujar()

    @staticmethod
    def preparar_tabla(tabla, titulos):
        for pos, titulo in enumerate(titulos):
            tabla.append_column(
                Gtk.TreeViewColumn(titulo, Gtk.CellRendererText(), text=pos)
            )

    def on_chmaquina_destroy(self, *args):
        Gtk.main_quit()

    def on_chmaquina_show(self, *args):
        self.on_tamano_memoria_value_changed(
            self.constructor.get_object("tamano-memoria")
        )

    def on_encender_clicked(self, widget):
        self.maquina = Maquina(
            tamano_kernel=self.preferencias["tamano_kernel"],
            tamano_memoria=self.preferencias["tamano_memoria"],
            teclado=TecladoGtk(self.ventana),
        )
        self.actualizar_estado(self.maquina.encender())

    def on_siguiente_clicked(self, widget):
        self.actualizar_estado(self.maquina.paso(self.estado))

    def on_continuo_clicked(self, widget):
        for estado in self.maquina.iterar(self.estado):
            self.actualizar_estado(estado)

    def on_apagar_clicked(self, widget):
        self.actualizar_estado(None)

    def on_cargar_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            "Por favor escoja un ch programa",
            self.ventana,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )
        filter_text = Gtk.FileFilter()
        filter_text.set_name("CH Programas")
        filter_text.add_pattern("*.ch")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Cualquier archivo")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            with open(dialog.get_filename()) as programa:
                self.actualizar_estado(
                    self.maquina.cargar(self.estado, programa.read())
                )

        dialog.destroy()

    def on_preferencias_clicked(self, widget):
        dialogo_preferencias = self.constructor.get_object("dialogo-preferencias")
        response = dialogo_preferencias.run()
        if response == Gtk.ResponseType.OK:
            self.preferencias["tamano_memoria"] = int(
                self.constructor.get_object("tamano-memoria").get_value()
            )
            self.preferencias["tamano_kernel"] = int(
                self.constructor.get_object("tamano-kernel").get_value()
            )
        self.redibujar()
        dialogo_preferencias.hide()

    def on_tamano_memoria_value_changed(self, ajuste_memoria):
        # Controlemos que el tamaño del kernel no se pueda hacer mayor que el tamaño
        # del la memoria
        ajuste_kernel = self.constructor.get_object("tamano-kernel")
        ajuste_kernel.set_value(
            min(ajuste_memoria.get_value(), ajuste_kernel.get_value())
        )
        ajuste_kernel.set_upper(ajuste_memoria.get_value())

    def actualizar_estado(self, estado):
        self.estado = estado
        self.redibujar()

    def habilitar_botones(self, activos):
        todos = [
            "encender",
            "preferencias",
            "apagar",
            "cargar",
            "siguiente",
            "continuo",
        ]
        for boton in todos:
            widget = self.constructor.get_object(boton)
            widget.set_sensitive(activos.get(boton, False))

    def redibujar(self):
        apagada = self.estado is None or self.maquina is None
        nada_por_hacer = self.estado and self.estado.nada_por_hacer()

        self.habilitar_botones(
            {
                "encender": apagada,
                "preferencias": apagada,
                "apagar": not apagada,
                "cargar": not apagada,
                "siguiente": not apagada and not nada_por_hacer,
                "continuo": not apagada and not nada_por_hacer,
            }
        )

        self.constructor.get_object("tamano-memoria").set_value(
            self.preferencias["tamano_memoria"]
        )
        self.constructor.get_object("tamano-kernel").set_value(
            self.preferencias["tamano_kernel"]
        )

        if apagada:
            # maquina apagada
            self.tabla_memoria.set_model(None)
            self.tabla_etiquetas.set_model(None)
            self.tabla_variables.set_model(None)
            self.tabla_programas.set_model(None)
            self.constructor.get_object("area-impresora").set_buffer(Gtk.TextBuffer())
            self.constructor.get_object("area-pantalla").set_buffer(Gtk.TextBuffer())
            for label in (
                "programa",
                "posicion",
                "contador",
                "tiempo",
                "instruccion",
                "acumulador",
            ):
                self.constructor.get_object(f"label-{label}").set_text("")
            return

        instruccion = self.estado.siguiente_instruccion()
        if instruccion is not None:
            programa, codigo = instruccion
            datos_programa = self.estado.programas[programa]
            posicion = datos_programa["inicio"] + datos_programa["contador"]
            self.constructor.get_object("label-programa").set_text(programa)
            self.constructor.get_object("label-tiempo").set_text(str(self.estado.reloj))
            self.constructor.get_object("label-posicion").set_text(f"{posicion:06d}")
            self.constructor.get_object("label-contador").set_text(
                str(datos_programa["contador"])
            )
            self.constructor.get_object("label-instruccion").set_text(codigo)
            self.constructor.get_object("label-acumulador").set_text(
                self.estado.buscar_variable(programa, "acumulador").get("valor", "")
            )

        store = Gtk.ListStore(str, str, str, str, str)
        for pos, item in enumerate(self.estado.memoria):
            if item:
                store.append(
                    [
                        f"{pos:06d}",
                        item.get("programa", ""),
                        item.get("tipo", ""),
                        item.get("nombre", ""),
                        item.get("valor", ""),
                    ]
                )
        self.tabla_memoria.set_model(store)

        store = Gtk.ListStore(str, str, str)
        for programa, etiquetas in self.estado.etiquetas.items():
            for nombre, pos in etiquetas.items():
                store.append([programa, nombre, f"{pos:06d}"])
        self.tabla_etiquetas.set_model(store)

        store = Gtk.ListStore(str, str, str)
        for programa, variables in self.estado.variables.items():
            for nombre, pos in variables.items():
                store.append([programa, nombre, f"{pos:06d}"])
        self.tabla_variables.set_model(store)

        # ["Programa", "Llegada", "Inicio", "Datos", "Fin", "Contador"],
        store = Gtk.ListStore(str, str, str, str, str, str)
        for nombre, datos in self.estado.programas.items():
            store.append(
                [
                    nombre,
                    str(datos["tiempo_llegada"]),
                    f"{datos['inicio']:06d}",
                    f"{datos['datos']:06d}",
                    f"{datos['final']:06d}",
                    str(datos["contador"]),
                ]
            )
        self.tabla_programas.set_model(store)

        for salida in ("impresora", "pantalla"):
            buffer = Gtk.TextBuffer()
            buffer.set_text(
                "\n".join(
                    f"[{programa}] {mensaje}"
                    for programa, mensaje in getattr(self.estado, salida)
                )
            )
            self.constructor.get_object(f"area-{salida}").set_buffer(buffer)


def main():
    constructor = Gtk.Builder()
    constructor.add_from_file("./ui/main.glade")
    constructor.connect_signals(InterfazChMaquina(constructor))

    window = constructor.get_object("chmaquina")
    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
