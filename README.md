# MiniScada

Pantalla de línea para un PLC Schneider TM221CE16R. Lee cinco datos por Modbus TCP y los muestra a pantalla completa. No escribe en el PLC.

## Qué se ve

| Zona | Significado |
|---|---|
| Cajas / min | Ritmo del último minuto. Es el recuadro con color |
| Paros (min) | Minutos acumulados sin pulsos del sensor |
| Paros (veces) | Cuántas veces se detuvo el conteo |
| Total | Todo lo que contó el sensor, con punto de miles (`16935` se ve `16.935`) |

El promedio del turno (total ÷ minutos) sigue calculándose, pero el recuadro está oculto. En **Ajustes**, la casilla **Mostrar promedio del turno** lo vuelve a enseñar y el color pasa a ese número.

Si el PLC no responde, aparece **Sin conexión**, los números quedan en gris y el promedio no se pinta de verde ni de rojo. Se conserva el último valor.

## Valores iniciales

Se cambian en el botón **Ajustes** de la pantalla. Quedan guardados en `config.json` y sobreviven a un reinicio.

- Verde desde **75** cajas/min
- Rojo por debajo de **60**
- De 60 a 74: ámbar
- **10** segundos sin pulso para contar un paro

El promedio en cero (turno recién reseteado) se queda en blanco, sin color.

Los segundos sin pulso los aplica el programa del PLC. La pantalla solo recuerda el número: al cambiarlo hay que dejar el mismo valor en el temporizador del sensor.

## Mapa Modbus

Dirección base 0. `%MW0` es el holding register 0. Una sola conexión TCP, puerto 502, unit id 1.

| Variable | Registro | Tipo |
|---|---|---|
| Total de cajas | `%MD0` (`%MW0` y `%MW1`) | entero 32 bits |
| Cajas / min | `%MW2` | entero 16 bits |
| Paros (min) | `%MW4` | entero 16 bits |
| Paros (veces) | `%MW6` | entero 16 bits |
| Minutos de turno | `%MW8` | entero 16 bits |

`%MW`, `%MD` y `%MF` comparten la misma memoria: estos registros no deben pisarse con otras variables. Las entradas `%I` y las salidas `%Q` no se leen por Modbus; el programa del PLC copia el conteo del sensor a `%MD0`.

El orden de las dos palabras del total está en `plc.word_order`. El valor inicial es `CDAB` (palabra baja en la dirección menor). Si el total sale disparatado, cámbialo a `ABCD` y reinicia.

En el PLC:

- Cada pulso suma una caja.
- Cada 60 segundos publica las cajas de ese minuto en `%MW2`.
- Si pasan los segundos configurados sin pulso, corre el tiempo de paro y, al entrar en paro, suma una vez a `%MW6`.
- Un botón de reset pone en cero el total, los paros y los minutos de turno.

La IP del PLC se cambia en `config.json`, campo `plc.host`. Hoy está en `192.168.0.10`.

## Probar en VS Code, sin PLC

En esta computadora ya está Python y el entorno `.venv`. No hace falta instalar NSSM, Edge ni el PLC para ver la pantalla.

1. En VS Code: **Archivo → Abrir carpeta** y elige `MiniScada`.
2. **Terminal → Nueva terminal** y ejecuta:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

3. Abre `http://127.0.0.1:8080` en el navegador.
4. Pulsa **Ajustes**, marca **Simular sin PLC** y **Guardar**.

Aparece el ejemplo de la foto (170, promedio 70, paros 98 y 59, total 16.935) con la franja **Simulación**. Baja el verde a 70 y el promedio pasa a verde. Súbelo otra vez a 75 y vuelve a ámbar. Quita la casilla para dejar de simular.

Si PowerShell no deja activar el entorno, no uses `Activate.ps1`: el comando de arriba llama al Python del entorno directo.

## Arranque

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.selftest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

La pantalla queda en `http://127.0.0.1:8080/`. `/health` responde aunque el PLC esté apagado.

## Servicio de Windows

El servicio arranca solo al encender la PC, sin sesión de usuario. No puede abrir una ventana.

1. Instala Python, crea el entorno e instala `requirements.txt` como arriba.
2. Descarga NSSM desde [https://nssm.cc/](https://nssm.cc/).
3. En una consola de administrador:

```powershell
.\scripts\install-service.ps1 -NssmPath C:\tools\nssm.exe
nssm start MiniScada
```

NSSM reinicia el proceso si se cae. Los logs quedan en `logs\`.

## Pantalla al reiniciar

Para que el monitor de la línea se abra solo hace falta una sesión. El servicio, en la sesión 0, no tiene escritorio.

1. Crea un usuario local sin permisos de administrador.
2. Activa el inicio de sesión automático de ese usuario (`netplwiz`, casilla de contraseña desmarcada).
3. Programa una tarea **al iniciar sesión** que ejecute `scripts\start-kiosk.ps1`.

Ese script espera a que `/health` responda y abre Edge en pantalla completa. Si la pantalla la van a ver desde otra PC o una tablet, basta el servicio y una regla de firewall para el puerto 8080. El puerto 502 no se abre en esta computadora: ella es cliente del PLC.
