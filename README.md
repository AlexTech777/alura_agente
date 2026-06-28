# 🤖 Alura Agente

Agente de inteligencia artificial que responde preguntas en lenguaje natural sobre la documentación interna de **NimbusFlow**, una plataforma SaaS ficticia de gestión de proyectos. El agente lee varios documentos PDF (uno por tema) usando RAG (Retrieval-Augmented Generation) con LangChain y Gemini, y se despliega en Oracle Cloud Infrastructure (OCI).

## 📐 Arquitectura

```
        ┌──────────────────────────────────────────────┐
        │                 data/*.pdf                   │
        │  base_conocimiento_producto.pdf              │
        │  faq_soporte.pdf                             │
        │  politica_privacidad.pdf                     │
        │  planes_y_precios.pdf                        │
        │  terminos_de_uso.pdf                         │
        └───────────────────┬──────────────────────────┘
                             │ PyPDFLoader (carga TODOS los PDFs de la carpeta)
                             ▼
                 ┌─────────────────┐
                 │  Text Splitter   │  (chunks de ~1000 caracteres, con metadata de origen)
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │ Gemini Embeddings│
                 └────────┬─────────┘
                          ▼
                 ┌─────────────────┐
                 │  Índice FAISS    │  (búsqueda por similitud, único índice para todos los PDFs)
                 └────────┬─────────┘
                          │
   Usuario ──pregunta──▶  │  ◀── recupera los 4 fragmentos más relevantes (de cualquier documento)
                          ▼
                 ┌─────────────────┐
                 │  Gemini (LLM)    │  genera la respuesta final
                 └────────┬─────────┘
                          ▼
                    Respuesta en
                   lenguaje natural
```

**Componentes:**
- **Carga y procesamiento**: `PyPDFLoader` + `RecursiveCharacterTextSplitter` (LangChain) leen **todos** los PDFs de la carpeta `data/` y los dividen en fragmentos, guardando el nombre del archivo de origen como metadata.
- **Embeddings**: `GoogleGenerativeAIEmbeddings` convierte cada fragmento en un vector.
- **Vector store**: `FAISS` indexa los vectores de todos los documentos en un único índice y permite buscar los fragmentos más relevantes para cada pregunta, sin importar de qué PDF vengan.
- **Generación**: `ChatGoogleGenerativeAI` (Gemini 1.5 Flash) recibe la pregunta + los fragmentos relevantes y genera la respuesta (patrón RAG).
- **Interfaz**: una app Flask (`app.py`) expone el agente como página web y como API JSON.

## 📁 Estructura del proyecto

```
alura_agente/
├── agent.py                       # Lógica del agente RAG (carga TODOS los PDFs de data/, indexa, responde)
├── app.py                         # App web Flask que expone el agente
├── generate_saas_pdfs.py          # Genera los 5 PDFs de ejemplo de NimbusFlow (SaaS)
├── data/
│   ├── base_conocimiento_producto.pdf
│   ├── faq_soporte.pdf
│   ├── politica_privacidad.pdf
│   ├── planes_y_precios.pdf
│   └── terminos_de_uso.pdf
├── requirements.txt
├── .env.example
└── README.md
```

## 📄 Documentos fuente (escenario: SaaS "NimbusFlow")

| Documento | Contenido |
|---|---|
| `base_conocimiento_producto.pdf` | Qué es la plataforma, módulos, roles de usuario, límites técnicos, SLA, exportación de datos |
| `faq_soporte.pdf` | Preguntas frecuentes: contraseñas, invitar miembros, automatizaciones, tiempos de soporte, migración de datos |
| `politica_privacidad.pdf` | Datos recopilados, finalidad, conservación, terceros, derechos del usuario, seguridad |
| `planes_y_precios.pdf` | Planes Free / Pro / Business / Enterprise, precios, prueba gratuita, descuentos |
| `terminos_de_uso.pdf` | Aceptación de términos, uso permitido, cancelación, reembolsos, suspensión, propiedad de datos |


## 🔑 Requisitos previos

- Python 3.10+
- Una clave de API de **Google Gemini** (gratuita): obtenela en https://aistudio.google.com/app/apikey

## ▶️ Ejecución local (probar primero, siempre)

```bash
git clone <tu-repo>
cd alura_agente

python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Editá .env y pegá tu clave: GOOGLE_API_KEY=AIza...

# (opcional, ya vienen incluidos) regenerar los PDFs de ejemplo:
python generate_saas_pdfs.py

# Opción A: agente por consola
export $(cat .env | xargs)   # carga la variable de entorno (Linux/Mac)
python agent.py

# Opción B: app web local
python app.py
# abrí http://localhost:8080
```

> 💡 **Tip**: para usar tus propios documentos, simplemente colocá tus PDFs dentro de la carpeta `data/` (el agente carga automáticamente todos los `.pdf` que encuentre ahí). Si cambiás los documentos, borrá `data/faiss_index/` para que se regenere el índice.

## 💬 Ejemplos de preguntas y respuestas

Con los documentos de ejemplo de NimbusFlow:

| Pregunta | Respuesta esperada |
|---|---|
| ¿Cuántos tableros puedo crear en el plan Free? | Hasta 3 tableros activos. |
| ¿Cuánto cuesta el plan Pro por persona usuaria? | 9 dólares/mes (facturación mensual) o 7 dólares/mes (facturación anual). |
| ¿Cómo recupero mi contraseña? | Desde la pantalla de inicio de sesión, con un enlace válido por 30 minutos. |
| ¿NimbusFlow vende mis datos a terceros? | No, no vende datos personales a terceros. |
| ¿Hay reembolso si cancelo después de un mes de uso? | Solo si la solicitud se hace dentro de los primeros 14 días desde el primer pago. |
| ¿Qué pasa si mi cuenta viola los términos de uso? | Puede suspenderse de inmediato, con notificación dentro de las 24 horas. |

## ☁️ Deploy en Oracle Cloud Infrastructure (OCI)

### 1. Crear la instancia de cómputo
1. En la consola de OCI: **Compute → Instances → Create Instance**.
2. Elegí una imagen **Ubuntu 22.04** (Always Free: shape `VM.Standard.E2.1.Micro`).
3. Agregá tu clave SSH pública.
4. En **Networking**, asegurate de que la instancia tenga una **IP pública**.

### 2. Abrir el puerto de la app en el Security List
1. Ve a tu VCN → Security Lists → la lista asociada a la subred.
2. Agregá una regla de **Ingress**: protocolo TCP, puerto destino `8080`, origen `0.0.0.0/0`.

### 3. Conectarte por SSH e instalar dependencias

```bash
ssh -i tu_clave.pem ubuntu@<IP_PUBLICA_DE_LA_INSTANCIA>

sudo apt update && sudo apt install -y python3-pip python3-venv git

# Si la instancia usa firewall propio (iptables/ufw), abrí el puerto también ahí:
sudo ufw allow 8080
```

### 4. Subir el proyecto y ejecutarlo

```bash
git clone <tu-repo>
cd alura_agente

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "GOOGLE_API_KEY=tu_clave" > .env
export $(cat .env | xargs)

# Para correrlo en background y que sobreviva al cierre de la sesión SSH:
nohup gunicorn -w 2 -b 0.0.0.0:8080 app:app > app.log 2>&1 &
```

### 5. Verificar el deploy

Abrí en el navegador: `http://<IP_PUBLICA_DE_LA_INSTANCIA>:8080`

Deberías ver la interfaz del Alura Agente funcionando públicamente. 📸 *(agregá aquí tu captura de pantalla o el enlace una vez desplegado)*

> 💡 Para que el servicio se reinicie solo si la instancia reinicia, lo ideal es crear un `systemd service` en vez de usar `nohup`, pero para este desafío `nohup` + `gunicorn` es suficiente.

## ✅ Checklist de entrega

- [x] Código que lee y procesa el documento (PDF).
- [x] Agente que responde preguntas en lenguaje natural sobre el documento.
- [x] Deploy en OCI Compute, accesible públicamente.
- [x] Repositorio en GitHub con historial de commits.
- [x] README con arquitectura, ejemplos y pasos de ejecución/deploy.

## 🛠️ Tecnologías usadas

Python · LangChain · PyPDF · FAISS · Gemini (Google Generative AI) · Flask · Gunicorn · Oracle Cloud Infrastructure (OCI Compute)
