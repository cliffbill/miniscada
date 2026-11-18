# Instalación de MiniScada en otra PC

Pantalla de línea para un PLC Schneider TM221CE16R. La PC lee el PLC por Modbus TCP cada medio segundo y muestra cuatro cifras en el navegador. La única escritura prevista es un bit de reset, y todavía no está programada: faltan la dirección y el comportamiento que indique el cliente.

En la PC de la línea la carpeta debe quedar en `C:\MiniScada`. Si se usa otra ruta, hay que cambiarla en todos los pasos de abajo.

## 1. Qué copiar

`dist` no se copia. Esa carpeta solo existe en esta PC, donde se armó el programa.

Se copia la carpeta de adentro, `dist\MiniScada`, la que contiene `MiniScada.exe`. En la otra PC esa carpeta se pega directo en `C:\` y queda así:

```
C:\MiniScada\
  MiniScada.exe
  config.json
  INSTALACION.md
  _internal\
  scripts\start-kiosk.ps1
```

`_internal` va junto con el exe. Si se copia solo `MiniScada.exe`, el programa no abre. No hace falta crear una carpeta `dist` en la otra PC.

Esa carpeta trae el programa, las librerías y la pantalla. No lleva los archivos `.py`. La otra PC no necesita Python.

## 2. Preparar la carpeta en esta PC

Esto se hace una vez, en la PC de desarrollo, antes de llevarla a la línea.

```powershell
cd C:\Users\billc\OneDrive\Documents\MiniScada
.\.venv\Scripts\python.exe -m pip install pyinstaller==6.16.0
.\.venv\Scripts\python.exe -m PyInstaller MiniScada.spec --noconfirm
```

El resultado queda en `dist\MiniScada`. Copia esa carpeta, no la carpeta `dist`, y en la otra PC déjala como `C:\MiniScada`.

## 3. En la otra PC

No se instala Python ni se ejecuta `pip`. Microsoft Edge ya viene con Windows.

La pantalla es la misma que en esta PC. El archivo HTML va dentro del programa, no como código suelto. Al abrir `http://127.0.0.1:8080` se ve igual y hace lo mismo:

- Cajas / min, a lo ancho, en verde, ámbar o rojo.
- Paros (min) y Paros (veces).
- Total, con punto de miles.
- Franja **Sin conexión** si el PLC no responde, o **Simulación** si esa casilla está marcada.
- Botón **Ajustes** para la meta, los segundos sin pulso, la simulación y, si hace falta, mostrar el promedio del turno.

Los valores se actualizan solos, sin recargar la página. Sigue en el paso 4.

## 4. Configurar `config.json`

Abre `C:\MiniScada\config.json` con el Bloc de notas. Ajusta esto antes de conectar el PLC:

```json
"host": "192.168.0.10",
"port": 502,
"unit_id": 1,
"poll_ms": 500,
"word_order": "CDAB",
"stop_gap_seconds": 10,
"demo": false,
"show_promedio": false,
"green_at": 75,
"red_below": 60
```

| Campo | Qué poner |
|---|---|
| `plc.host` | IP real del TM221. La PC y el PLC tienen que verse en la red. |
| `plc.port` | `502`, salvo que en el PLC se haya cambiado. |
| `plc.unit_id` | `1`, salvo que en Machine Expert se haya cambiado. |
| `plc.poll_ms` | `500`. La pantalla se actualiza cada medio segundo. |
| `plc.word_order` | `CDAB`. Si el total sale disparatado y las demás cifras se ven bien, cámbialo a `ABCD` y reinicia el programa. |
| `plc.stop_gap_seconds` | Segundos sin pulso del sensor para contar un paro. El PLC es quien aplica este tiempo. Aquí solo queda anotado. El valor de partida es `10`. |
| `demo` | `false` en la línea. Con `true` muestra números de prueba y no lee el PLC. |
| `show_promedio` | `false`. La pantalla enseña solo las cuatro cifras. |
| `green_at` | Cajas/min desde las que el recuadro queda verde. Partida: `75`. |
| `red_below` | Por debajo de este número queda rojo. Partida: `60`. Entre los dos queda ámbar. El verde tiene que ser mayor que el rojo. |

Guarda el archivo.

Estos tres valores también se pueden cambiar después en el botón **Ajustes** de la pantalla, sin editar el archivo: verde, rojo y segundos sin pulso. Quedan guardados y sobreviven a un reinicio.

## 5. Qué tiene que tener el PLC

La pantalla lee el conteo y los paros. Esos acumulados viven en el programa del PLC. El reset, cuando se programe, será un bit que la pantalla pone en 1 un instante. El PLC limpia los contadores y devuelve el bit a 0.

| En pantalla | Registro | Tipo |
|---|---|---|
| Total de cajas | `%MD0` (`%MW0` y `%MW1`) | entero de 32 bits |
| Cajas / min | `%MW2` | entero de 16 bits |
| Paros (min) | `%MW4` | entero de 16 bits |
| Paros (veces) | `%MW6` | entero de 16 bits |
| Minutos de turno | `%MW8` | entero de 16 bits. No se muestra. Sirve para el promedio oculto. |

`%MW0` es el holding register 0. Esas direcciones no deben pisarse con otras variables: `%MW`, `%MD` y `%MF` comparten la misma memoria.

Las entradas `%I` y las salidas `%Q` no se leen por Modbus. El programa del PLC copia el conteo del sensor a `%MD0`.

Si el programa nunca escribe una de esas direcciones, esa cifra sale en 0 y las demás siguen. La pantalla entera se pone en **Sin conexión** solo si falla la lectura completa: IP mal, PLC apagado o unit id distinto.

## 5.1 Reset desde la pantalla (pendiente)

Sí se puede escribir un bit en el TM221 por Modbus TCP. Todavía no está en el programa. Se agrega cuando lleguen estos datos:

| Dato | Para qué sirve | Estado |
|---|---|---|
| Dirección del bit | `%M` (bobina) o un bit de un `%MW`. Ejemplo: `%M100`. | Pendiente |
| Quién lo apaga | Lo normal: la pantalla lo pone en 1, el PLC limpia los contadores y lo regresa a 0. | Pendiente |
| Qué se pone en cero | Total, paros en minutos, paros en veces, minutos de turno y el ritmo del último minuto. | Pendiente |
| Confirmación | Un botón **Reset** en la pantalla, con una pregunta de confirmación, solo si el PLC está en línea. | Por definir |

El bit no puede quedarse en 1. Si se queda, el PLC volvería a borrar los contadores en cada ciclo.

Hasta tener la dirección, el reset sigue siendo un botón físico en la máquina, hecho en el programa del PLC.

## 6. Probar a mano

En `C:\MiniScada` haz doble clic en `MiniScada.exe`.

Cuando la ventana diga que está en marcha, abre [http://127.0.0.1:8080](http://127.0.0.1:8080).

- Con el PLC en línea se ven las cuatro cifras y Cajas/min en color.
- Sin PLC aparece **Sin conexión** y los números en gris. El programa reintenta solo.
- Para ver un ejemplo sin PLC: **Ajustes**, marca **Simular sin PLC** y guarda. En la línea esa casilla tiene que quedar apagada.

Cierra esa ventana al terminar la prueba. El paso 7 la deja encendida sin tener que abrirla a mano.

## 7. Que arranque sola al reiniciar

Son dos tareas. La primera enciende el programa. La segunda abre la pantalla. El programa, por sí solo, no puede abrir una ventana.

Cierra antes la ventana de PowerShell de la prueba. Si sigue abierta, el puerto 8080 queda ocupado.

### 7.1 Programa al encender

1. Pulsa la tecla Windows, escribe **Programador de tareas** y ábrelo.
2. A la derecha pulsa **Crear tarea**. No uses "Crear tarea básica".
3. En **General**:
   - Nombre: `MiniScada`
   - Marca **Ejecutar tanto si el usuario inició sesión como si no**
4. En **Desencadenadores**, **Nuevo**:
   - Iniciar la tarea: **Al iniciar el sistema**
   - Aceptar
5. En **Acciones**, **Nueva**:
   - Acción: **Iniciar un programa**
   - Programa: `C:\MiniScada\MiniScada.exe`
   - Argumentos: déjalos vacíos
   - Iniciar en: `C:\MiniScada`
6. En **Condiciones**, quita **Iniciar la tarea solo si el equipo está conectado a la corriente alterna**.
7. Aceptar y escribe la contraseña de Windows de esa PC.

Para probarla sin reiniciar: clic derecho en la tarea `MiniScada`, **Ejecutar**, y abre [http://127.0.0.1:8080](http://127.0.0.1:8080).

### 7.2 Pantalla al iniciar sesión

1. Crea un usuario de Windows solo para el monitor, sin permisos de administrador.
2. Pulsa `Windows + R`, escribe `netplwiz` y Enter.
3. Elige ese usuario, desmarca **Los usuarios deben escribir su nombre y contraseña para usar el equipo**, acepta y escribe su contraseña. Así entra solo al encender.
4. En el Programador de tareas, **Crear tarea**:
   - Nombre: `MiniScada Pantalla`
   - Desencadenador: **Al iniciar sesión**, con ese usuario
   - Acción: **Iniciar un programa**
   - Programa: `powershell.exe`
   - Argumentos: `-ExecutionPolicy Bypass -File C:\MiniScada\scripts\start-kiosk.ps1`
   - Marca **Ejecutar solo cuando el usuario haya iniciado sesión**

Ese script espera a que el programa responda y abre Edge en pantalla completa.

Al reiniciar, el orden es: Windows enciende el programa, entra el usuario solo y Edge muestra la línea.

## 8. Lo que se ve

| Zona | Significado |
|---|---|
| Cajas / min | Ritmo del último minuto. Es el recuadro con color. |
| Paros (min) | Minutos acumulados sin pulsos del sensor. |
| Paros (veces) | Cuántas veces se detuvo el conteo. |
| Total | Todo lo que contó el sensor. `16935` se ve `16.935`. |

Verde: cajas/min mayor o igual que `green_at`. Rojo: por debajo de `red_below`. En medio: ámbar.

El promedio del turno (total ÷ minutos) se sigue calculando, pero el recuadro está oculto. En **Ajustes**, **Mostrar promedio del turno** lo vuelve a enseñar y el color pasa a ese número.

## 9. Si algo falla

| Lo que pasa | Qué revisar |
|---|---|
| No existe `MiniScada.exe` | En la PC de desarrollo falta generar `dist\MiniScada` con el paso 2. |
| **Sin conexión** con el PLC encendido | IP en `plc.host`, mismo cable o red, puerto 502, `unit_id` y `"demo": false`. Cierra el programa y ábrelo de nuevo después de cambiar la IP. |
| Números de ejemplo fijos (170, 98, 59, 16.935) y franja **Simulación** | **Ajustes**, quita **Simular sin PLC**. |
| El total es un número enorme y el resto se ve bien | En `config.json` cambia `word_order` a `ABCD` y reinicia el programa. |
| El puerto ya está en uso | Ya hay una copia corriendo. Cierra la ventana de `MiniScada.exe` o termina la tarea `MiniScada` antes de abrir otra. |
| La PC reinicia y no hay pantalla | La tarea `MiniScada` enciende el programa. La tarea `MiniScada Pantalla` abre Edge. Hacen falta las dos, más el inicio de sesión automático. |
