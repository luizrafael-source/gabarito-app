import sys

import cv2
import numpy as np
import pytesseract
import streamlit as st

# No Windows, aponte para onde o Tesseract foi instalado.
# Se você instalou em outro lugar, mude este caminho.
# No servidor (Linux) não precisa: o Tesseract já fica no PATH.
if sys.platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preparar_imagem(foto):
    """Deixa a imagem mais fácil de ler: cinza, maior e só preto e branco."""
    bytes_da_foto = np.frombuffer(foto.getvalue(), dtype=np.uint8)
    imagem = cv2.imdecode(bytes_da_foto, cv2.IMREAD_COLOR)

    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    cinza = cv2.resize(cinza, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    cinza = cv2.GaussianBlur(cinza, (3, 3), 0)

    pb = cv2.adaptiveThreshold(
        cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )
    return pb


def ler_letras(foto):
    """Roda o OCR e devolve só as letras A, B, C e D encontradas."""
    imagem = preparar_imagem(foto)
    config = "--psm 6 -c tessedit_char_whitelist=ABCDabcd"
    texto = pytesseract.image_to_string(imagem, config=config)
    return "".join(c.upper() for c in texto if c in "ABCDabcd")


def limpar(texto):
    """Mantém só A, B, C e D (ignora espaços, números, vírgulas)."""
    return [c for c in texto.upper() if c in "ABCD"]


st.title("Conferidor de gabarito (versão gratuita)")

st.info(
    "Dica: antes de enviar, corte a foto para mostrar SÓ a linha com as letras. "
    "Textos e números em volta atrapalham a leitura."
)

total = st.number_input("Quantidade de questões", min_value=1, max_value=100, value=36)

foto_gabarito = st.file_uploader("Foto do gabarito oficial (recortada)", type=["jpg", "jpeg", "png"])
foto_aluno = st.file_uploader("Foto das suas respostas (recortada)", type=["jpg", "jpeg", "png"])

if st.button("Ler as fotos"):
    if foto_gabarito and foto_aluno:
        with st.spinner("Lendo as fotos..."):
            st.session_state["gabarito"] = ler_letras(foto_gabarito)
            st.session_state["aluno"] = ler_letras(foto_aluno)
    else:
        st.warning("Envie as duas fotos primeiro.")

if "gabarito" in st.session_state:
    st.subheader("Confira e corrija a leitura")
    st.caption(
        "O OCR erra bastante com letra à mão. Compare com a foto e corrija aqui."
    )

    gab_texto = st.text_input("Gabarito oficial", st.session_state["gabarito"])
    aluno_texto = st.text_input("Suas respostas", st.session_state["aluno"])

    gab = limpar(gab_texto)
    aluno = limpar(aluno_texto)

    st.write(f"Letras no gabarito: {len(gab)} | Letras nas suas respostas: {len(aluno)} | Esperado: {total}")

    if len(gab) != len(aluno):
        st.warning("As duas listas precisam ter o mesmo tamanho. Ajuste as letras acima.")
    elif st.button("Calcular"):
        acertos = 0
        erros = []

        for i in range(len(gab)):
            if gab[i] == aluno[i]:
                acertos += 1
            else:
                erros.append(f"Questão {i + 1}: você marcou {aluno[i]}, o certo é {gab[i]}")

        st.success(f"Acertos: {acertos} de {len(gab)}")
        if erros:
            st.write("Erros:")
            for e in erros:
                st.write("- " + e)
