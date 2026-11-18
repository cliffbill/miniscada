# Arranque automático de MiniScada

En esta PC el programa está en `C:\MiniScada\MiniScada.exe`. La pantalla se abre en el navegador, en [http://127.0.0.1:8080](http://127.0.0.1:8080).

`MiniScada.exe` es un programa de consola. Mientras la ventana de consola sigue abierta, MiniScada está en marcha. Al cerrar esa ventana, MiniScada se detiene.

Esta página cubre dos casos: volver a abrirlo si se cerró la consola, y dejarlo para que Windows lo abra al iniciar sesión.

## 1. Si se cerró la ventana de consola

1. Con la consola cerrada, MiniScada está detenido.
2. Abre el navegador y entra en [http://127.0.0.1:8080](http://127.0.0.1:8080).
3. Si el tablero ya aparece, MiniScada ya está en marcha. Deja esa copia. En esta PC corre una sola a la vez.
4. Si la página no abre, haz doble clic en `C:\MiniScada\MiniScada.exe`.
5. Deja esa ventana de consola abierta.
6. Vuelve al navegador y entra en [http://127.0.0.1:8080](http://127.0.0.1:8080).

## 2. Que arranque al iniciar sesión

Al reiniciar la PC, MiniScada queda detenido. Windows lo abre al iniciar sesión cuando esta tarea está creada. Se configura una sola vez, en el **Programador de tareas** (Task Scheduler), con la cuenta de la persona que usa esta PC.

La tarea usa **Al iniciar sesión** (At log on). Así la ventana de consola queda en el escritorio y el navegador de esa sesión puede abrir la pantalla.

### 2.1 Crear la tarea

1. Pulsa la tecla Windows, escribe **Programador de tareas** y ábrelo.
2. En el panel de la derecha, pulsa **Crear tarea...** (Create Task).
3. En la pestaña **General**:
   - Nombre: `MiniScada`
   - Marca **Ejecutar solo cuando el usuario haya iniciado sesión** (Run only when user is logged on).
   - Arriba aparece la cuenta con la que estás. Si es la de quien usa esta PC, déjala.

### 2.2 Desencadenador

1. Abre la pestaña **Desencadenadores** (Triggers).
2. Pulsa **Nuevo...** (New).
3. En **Iniciar la tarea** (Begin the task), elige **Al iniciar sesión** (At log on).
4. Elige **Usuario o grupo específico** (Specific user or group) y deja la cuenta de quien usa esta PC.
5. Pulsa **Aceptar**.

### 2.3 Acción

1. Abre la pestaña **Acciones** (Actions).
2. Pulsa **Nueva...** (New).
3. En **Acción**, elige **Iniciar un programa** (Start a program).
4. En **Programa o script** (Program/script), escribe:

   `C:\MiniScada\MiniScada.exe`

5. En **Iniciar en (opcional)** (Start in), escribe:

   `C:\MiniScada`

6. Deja **Agregar argumentos** vacío.
7. Pulsa **Aceptar**.

### 2.4 Configuración

1. Abre la pestaña **Configuración** (Settings).
2. En **Si la tarea ya se está ejecutando, se aplica la siguiente regla** (If the task is already running, then the following rule applies), elige **No iniciar una nueva instancia** (Do not start a new instance).
3. Marca **Si se produce un error en la tarea, reiniciarla cada** (If the task fails, restart every). Pon **1 minuto**. En **Intentar reiniciar hasta** (Attempt to restart up to), pon **3** veces.
4. Quita la marca de **Detener la tarea si se ejecuta durante más de** (Stop the task if it runs longer than). MiniScada puede quedarse abierto todo el turno.
5. Deja marcada **Permitir que la tarea se ejecute a petición** (Allow task to be run on demand).
6. Pulsa **Aceptar**.

### 2.5 La ventana de consola

Al iniciar sesión aparece la ventana de consola de MiniScada. Eso es lo esperado: esa ventana es el programa en marcha.

MiniScada sigue mientras esa ventana permanece abierta. Si la cierras durante el turno, el programa se detiene; para seguir en ese turno usa el apartado 1. En el siguiente inicio de sesión, la tarea lo abre otra vez.

### 2.6 Probar sin reiniciar

1. Si habías abierto MiniScada a mano, cierra esa ventana de consola y espera a que desaparezca. La prueba arranca una sola copia, la de la tarea.
2. En el Programador de tareas, abre **Biblioteca del Programador de tareas** (Task Scheduler Library).
3. Selecciona la tarea **MiniScada**.
4. En el panel de la derecha, pulsa **Ejecutar** (Run).
5. Aparece la ventana de consola. Déjala abierta.
6. Abre el navegador en [http://127.0.0.1:8080](http://127.0.0.1:8080).

Si el tablero ya estaba visible antes de pulsar **Ejecutar**, MiniScada ya estaba en marcha. En ese caso deja esa copia.

### 2.7 Detenerlo

Con la tarea **MiniScada** seleccionada, pulsa **Finalizar** (End).

También se detiene al cerrar la ventana de consola.

### 2.8 Quitar el arranque automático

- **Deshabilitar** (Disable) guarda la tarea y el inicio de sesión ya no abre MiniScada.
- **Eliminar** (Delete) quita la tarea.

Para usarlo a mano después de eso, haz doble clic en `C:\MiniScada\MiniScada.exe` y deja la consola abierta.

## 3. El escritorio al volver la corriente

La pantalla aparece cuando Windows ya inició sesión en esta PC. Si además quieres que, al volver la luz, la PC llegue sola al escritorio, eso se configura aparte en el inicio de sesión automático de Windows, con la cuenta de quien usa esta PC; la contraseña se escribe solo en esa pantalla de Windows.
