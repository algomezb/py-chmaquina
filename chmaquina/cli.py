import click


@click.group()
def main():
    """
    Script para ejecutar ch-programas.
    """
    click.echo("Ejecuto ch maquinas.")


@main.command()
def ui():
    """
    Script para ejecutar la UI del chmaquina.
    """
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    from chmaquina.interfaz import InterfazChMaquina

    constructor = Gtk.Builder()
    constructor.add_from_file("./ui/main.glade")
    constructor.connect_signals(InterfazChMaquina(constructor))

    window = constructor.get_object("chmaquina")
    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
