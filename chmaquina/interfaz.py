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


class ImpresoraGtk:
    def __init__(self, area_de_texto):
        self.area_de_texto = area_de_texto
        self.buffer = Gtk.TextBuffer()
        self.area_de_texto.set_buffer(self.buffer)

    def imprima(self, mensaje):
        final = self.buffer.get_end_iter()
        self.buffer.insert(final, f"{mensaje}\n")


class PantallaGtk:
    def __init__(self, area_de_texto):
        self.area_de_texto = area_de_texto
        self.buffer = Gtk.TextBuffer()
        self.area_de_texto.set_buffer(self.buffer)

    def muestre(self, mensaje):
        final = self.buffer.get_end_iter()
        self.buffer.insert(final, f"{mensaje}\n")


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
        self.preparar_tabla(
            self.tabla_memoria, ["Posición", "Programa", "Tipo", "Valor"]
        )
        self.preparar_tabla(self.tabla_variables, ["Programa", "Nombre", "Posición"])
        self.preparar_tabla(self.tabla_etiquetas, ["Programa", "Nombre", "Posición"])
        self.redibujar()

    @staticmethod
    def preparar_tabla(tabla, titulos):
        for pos, titulo in enumerate(titulos):
            tabla.append_column(
                Gtk.TreeViewColumn(titulo, Gtk.CellRendererText(), text=pos)
            )

    def on_chmaquina_destroy(self, *args):
        Gtk.main_quit()

    def on_encender_clicked(self, widget):
        self.maquina = Maquina(
            tamano_kernel=128,
            tamano_memoria=1024,
            teclado=TecladoGtk(self.ventana),
            impresora=ImpresoraGtk(self.constructor.get_object("area-impresion")),
            pantalla=PantallaGtk(self.constructor.get_object("area-pantalla")),
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
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            with open(dialog.get_filename()) as programa:
                self.actualizar_estado(
                    self.maquina.cargar(self.estado, programa.read())
                )

        dialog.destroy()

    def actualizar_estado(self, estado):
        self.estado = estado
        self.redibujar()

    def habilitar_botones(self, activos):
        todos = ["encender", "apagar", "cargar", "siguiente", "continuo"]
        for boton in todos:
            widget = self.constructor.get_object(boton)
            widget.set_sensitive(activos.get(boton, False))

    def redibujar(self):
        apagada = self.estado is None or self.maquina is None
        nada_por_hacer = self.estado and self.estado.nada_por_hacer()

        self.habilitar_botones(
            {
                "encender": apagada,
                "apagar": not apagada,
                "cargar": not apagada,
                "siguiente": not apagada and not nada_por_hacer,
                "continuo": not apagada and not nada_por_hacer,
            }
        )

        if apagada:
            # maquina apagada
            self.tabla_memoria.set_model(None)
            self.tabla_etiquetas.set_model(None)
            self.tabla_variables.set_model(None)
            self.constructor.get_object("area-impresion").set_buffer(Gtk.TextBuffer())
            self.constructor.get_object("area-pantalla").set_buffer(Gtk.TextBuffer())
            return

        store = Gtk.ListStore(str, str, str, str)
        for pos, item in enumerate(self.estado.memoria):
            if item:
                store.append(
                    [
                        f"{pos:04d}",
                        item.get("programa", ""),
                        item.get("tipo", ""),
                        item.get("valor", ""),
                    ]
                )
        self.tabla_memoria.set_model(store)

        store = Gtk.ListStore(str, str, str)
        for programa, etiquetas in self.estado.etiquetas.items():
            for nombre, pos in etiquetas.items():
                store.append([programa, nombre, f"{pos:04d}"])
        self.tabla_etiquetas.set_model(store)

        store = Gtk.ListStore(str, str, str)
        for programa, variables in self.estado.variables.items():
            for nombre, pos in variables.items():
                store.append([programa, nombre, f"{pos:04d}"])
        self.tabla_variables.set_model(store)
