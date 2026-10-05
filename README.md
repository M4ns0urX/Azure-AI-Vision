# Inova Trônica — Descrição de Imagens com Azure AI Vision

MVP que envia uma foto (arquivo local ou URL) ao serviço de Visão Computacional
da Azure e exibe a descrição gerada, a confiança e as tags detectadas.

## Recurso na Azure
- Grupo de recursos: `rg-vc-inova`
- Nome: `visao-inova-rmXXXX`
- Camada: Free (F0)

## Como executar
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # e preencha endpoint e chave
streamlit run app.py
```

## Tecnologias
Python, Streamlit e API REST do Azure AI Vision (Analyze v3.2 e Image Analysis 4.0).
