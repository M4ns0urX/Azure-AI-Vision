"""
Inova Trônica - MVP de Serviço Cognitivo
Envia uma imagem (upload local ou URL) ao Azure AI Vision e mostra a descrição.

Executar:  streamlit run app.py
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT", "").rstrip("/")
KEY = os.getenv("AZURE_VISION_KEY", "")
TIMEOUT = 30


# ---------------------------------------------------------------------------
# Chamadas à API (REST puro, sem SDK)
# ---------------------------------------------------------------------------
def _montar_requisicao(imagem_bytes: bytes | None, imagem_url: str | None):
    """Define headers e corpo conforme a origem da imagem."""
    headers = {"Ocp-Apim-Subscription-Key": KEY}
    if imagem_bytes is not None:
        headers["Content-Type"] = "application/octet-stream"
        return headers, {"data": imagem_bytes}
    headers["Content-Type"] = "application/json"
    return headers, {"json": {"url": imagem_url}}


def analisar_v4(imagem_bytes=None, imagem_url=None) -> dict:
    """Image Analysis 4.0 (legenda em inglês; disponível só em algumas regiões)."""
    url = f"{ENDPOINT}/computervision/imageanalysis:analyze"
    params = {
        "api-version": "2024-02-01",
        "features": "caption,tags",
        "language": "en",
        "gender-neutral-caption": "true",
    }
    headers, corpo = _montar_requisicao(imagem_bytes, imagem_url)
    resp = requests.post(url, params=params, headers=headers, timeout=TIMEOUT, **corpo)
    resp.raise_for_status()
    dados = resp.json()

    legenda = dados.get("captionResult", {})
    tags = dados.get("tagsResult", {}).get("values", [])
    return {
        "descricao": legenda.get("text", "(sem descrição)"),
        "confianca": legenda.get("confidence", 0.0),
        "tags": [(t["name"], t["confidence"]) for t in tags],
        "bruto": dados,
    }


def analisar_v32(imagem_bytes=None, imagem_url=None, idioma="pt") -> dict:
    """Analyze v3.2 (funciona em qualquer região e aceita descrição em português)."""
    url = f"{ENDPOINT}/vision/v3.2/analyze"
    params = {"visualFeatures": "Description,Tags", "language": idioma}
    headers, corpo = _montar_requisicao(imagem_bytes, imagem_url)
    resp = requests.post(url, params=params, headers=headers, timeout=TIMEOUT, **corpo)
    resp.raise_for_status()
    dados = resp.json()

    legendas = dados.get("description", {}).get("captions", [])
    melhor = legendas[0] if legendas else {"text": "(sem descrição)", "confidence": 0.0}
    tags = dados.get("tags", [])
    return {
        "descricao": melhor["text"],
        "confianca": melhor["confidence"],
        "tags": [(t["name"], t["confidence"]) for t in tags],
        "bruto": dados,
    }


def mensagem_de_erro(exc: requests.HTTPError) -> str:
    try:
        erro = exc.response.json().get("error", {})
        return f"{exc.response.status_code} - {erro.get('code', '')}: {erro.get('message', '')}"
    except ValueError:
        return f"{exc.response.status_code} - {exc.response.text[:300]}"


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Inova Trônica | Visão Computacional", page_icon="👁️")
st.title("👁️ Inova Trônica — Descrição de Imagens")
st.caption("MVP de Serviços Cognitivos com Azure AI Vision")

with st.sidebar:
    st.header("Configuração")
    if ENDPOINT and KEY:
        st.success("Credenciais carregadas do .env")
        st.text(f"Endpoint:\n{ENDPOINT}")
        st.text(f"Chave: {KEY[:4]}{'*' * 20}")
    else:
        st.error("Defina AZURE_VISION_ENDPOINT e AZURE_VISION_KEY no arquivo .env")

    versao = st.radio(
        "Versão da API",
        ["v3.2 (descrição em português)", "v4.0 (descrição em inglês)"],
        help="A v4.0 só gera legenda em algumas regiões da Azure. "
        "Se der erro de região, use a v3.2.",
    )

origem = st.radio("Origem da imagem", ["Arquivo local", "URL"], horizontal=True)

imagem_bytes, imagem_url = None, None
if origem == "Arquivo local":
    arquivo = st.file_uploader("Escolha uma foto", type=["jpg", "jpeg", "png", "bmp", "gif"])
    if arquivo:
        imagem_bytes = arquivo.getvalue()
        st.image(imagem_bytes, caption=arquivo.name, use_container_width=True)
else:
    imagem_url = st.text_input("URL pública da imagem", placeholder="https://...")
    if imagem_url:
        st.image(imagem_url, use_container_width=True)

pronto = (imagem_bytes or imagem_url) and ENDPOINT and KEY
if st.button("Analisar imagem", type="primary", disabled=not pronto):
    with st.spinner("Enviando ao serviço cognitivo..."):
        try:
            if versao.startswith("v4.0"):
                resultado = analisar_v4(imagem_bytes, imagem_url)
            else:
                resultado = analisar_v32(imagem_bytes, imagem_url)
        except requests.HTTPError as exc:
            st.error(f"Erro da API: {mensagem_de_erro(exc)}")
            st.stop()
        except requests.RequestException as exc:
            st.error(f"Falha de conexão: {exc}")
            st.stop()

    st.subheader("Descrição")
    st.markdown(f"### “{resultado['descricao']}”")
    st.progress(resultado["confianca"], text=f"Confiança: {resultado['confianca']:.1%}")

    if resultado["tags"]:
        st.subheader("Tags detectadas")
        st.write(" · ".join(f"`{nome}` ({conf:.0%})" for nome, conf in resultado["tags"][:15]))

    with st.expander("Resposta JSON completa da API"):
        st.json(resultado["bruto"])
