# Instalación de MiniScada en la otra PC

Pasos para copiar el programa a la PC de la línea y abrir la pantalla. En esa PC se usa `MiniScada.exe`.

## 1. Qué copiar

En esta PC, copia la carpeta completa:

`C:\Users\billc\OneDrive\Documents\MiniScada\dist\MiniScada`

Es la carpeta que contiene `MiniScada.exe`. Cópiala entera. Adentro tienen que estar:

- `MiniScada.exe`
- la carpeta `_internal`
- `config.json`
- la carpeta `img`, con `logo.jpeg` y `logo2.jpeg`

`_internal` viaja junto con el exe. El programa abre con esa carpeta completa.

## 2. Dónde ponerla

En la otra PC, pega esa carpeta de modo que quede así:

`C:\MiniScada\MiniScada.exe`

La carpeta se llama `MiniScada` y queda directo en `C:\`.

Si en esa PC ya existe `C:\MiniScada`, cierra MiniScada si está abierto y sustituye esa carpeta por la que acabas de copiar.

## 3. Red en la otra PC

Conecta un cable Ethernet de esa PC directo al PLC.

En el adaptador de ese cable, fija esta dirección:

1. Abre **Configuración**, entra en **Red e Internet** y elige **Ethernet**. También puedes usar **Centro de redes y recursos compartidos** y luego **Cambiar configuración del adaptador**.
2. Abre el adaptador Ethernet del cable que va al PLC y entra en **Propiedades**.
3. Selecciona **Protocolo de Internet versión 4 (TCP/IPv4)** y pulsa **Propiedades**.
4. Marca **Usar la siguiente dirección IP**.
5. Dirección IP: `192.168.10.100`
6. Máscara de subred: `255.255.255.0`
7. Deja la puerta de enlace vacía. Con el cable directo bastan la IP y la máscara.
8. Pulsa **Aceptar**.

El PLC permanece en `192.168.10.10`. Ese dato ya está en `config.json`. Los datos del PLC llegan por ese cable Ethernet.

## 4. Cómo arrancar

1. Haz doble clic en `C:\MiniScada\MiniScada.exe`.
2. Se abre una ventana de consola y se queda abierta. Déjala abierta mientras uses la pantalla.
3. Si Windows muestra el aviso del Firewall, permite MiniScada en las redes privadas. El programa escucha en `0.0.0.0:8080`. El navegador de esta misma PC usa `http://127.0.0.1:8080`.
4. Abre el navegador de esa PC y entra en [http://127.0.0.1:8080](http://127.0.0.1:8080).

## 5. Cómo confirmar que quedó instalado

El navegador muestra el tablero a pantalla completa: los logos, **GPM**, **Máquina**, **Cajas**, **Paros** y **Tiempo en paro**.

Con el cable conectado y el PLC encendido, aparecen los números.

Si el cable está fuera, la franja superior dice **Sin conexión**. Esa pantalla confirma que el programa quedó instalado.

## 6. Cómo detenerlo

Cierra la ventana de consola, o cierra MiniScada desde la barra de tareas.

Si se cierra la consola o si la PC se reinicia, los pasos están en `ARRANQUE-AUTOMATICO.md`, en esta misma carpeta.
