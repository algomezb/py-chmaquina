import pytest

from chmaquina.maquina import Maquina


@pytest.fixture
def maquina():
    return Maquina(tamano_memoria=1024, tamano_kernel=128)


def test_encender(maquina):
    estado = maquina.encender()
    assert len(estado.memoria) == maquina.tamano_memoria
    assert estado.contador == maquina.tamano_kernel + 1
    assert estado.pivote == maquina.tamano_kernel + 1


def test_paso_sin_programa(maquina):
    estado = maquina.encender()
    siguiente = maquina.paso(estado)
    assert estado == siguiente


def test_cargar_programa(maquina):
    instrucciones = ["nueva variable C hola que hace", "etiqueta fin 3", "retorne 0"]
    programa = "\n".join(instrucciones)
    num_variables = 1
    estado = maquina.encender()
    siguiente = maquina.cargar(estado, programa)
    assert siguiente.contador == estado.contador
    assert siguiente.pivote == estado.pivote + len(instrucciones) + num_variables
    assert siguiente.variables == {"000": {"variable": siguiente.pivote - 1}}
    assert siguiente.etiquetas == {"000": {"fin": estado.pivote + 3}}
