from __future__ import annotations

import io
from datetime import date
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st


# CONFIGURAÇÕES DA BARRA

st.set_page_config(
    page_title="Auditoria de Tábuas Biométricas",
    page_icon="📊",
    layout="wide"
)

# Estilização CSS 
st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
        }
        .stMetric {
            background-color: #ffffff !important;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #d1d5db !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .stMetric label {
            color: #4b5563 !important;
            font-weight: 600 !important;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #111827 !important;
        }
        .stButton > button {
            border-radius: 6px;
            font-weight: 600;
        }
        div[data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #1f2937;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Teste de Aderência de Tábuas Biométricas")

st.caption(
    "Ferramenta desenvolvida para Análise de Dados,"
    " processamento, limpeza, cálculo de expostos ao risco e auditoria de mortalidade"
)

MAX_AGE = 126


# FUNÇÕES AUXILIARES

def normalizar_nome_coluna(x: str) -> str:
    return str(x).replace("", "").strip()


def ler_csv(upload, nome: str) -> pd.DataFrame:
    """Lê arquivos CSV com delimitadores e codificações comuns."""

    for enc in ("latin1", "utf-8-sig", "cp1252"):

        for sep in (";", ",", " "):

            try:
                upload.seek(0)

                df = pd.read_csv(
                    upload,
                    sep=sep,
                    encoding=enc,
                    dtype=str,
                    low_memory=False
                )

                if len(df.columns) > 1:

                    df.columns = [
                        normalizar_nome_coluna(c)
                        for c in df.columns
                    ]

                    return df

            except Exception:
                continue

    raise ValueError(
        f"Não foi possível ler {nome}. "
        "Verifique o delimitador e a codificação."
    )


def exigir_colunas(
    df: pd.DataFrame,
    colunas: Iterable[str],
    nome: str
):

    faltantes = [
        c for c in colunas
        if c not in df.columns
    ]

    if faltantes:

        raise ValueError(
            f"Arquivo {nome}: faltam as colunas {faltantes}."
        )


def data_flexivel(serie: pd.Series) -> pd.Series:

    s = (
        serie.astype("string")
        .str.strip()
        .replace({
            "": pd.NA,
            "nan": pd.NA,
            "None": pd.NA
        })
    )

    return pd.to_datetime(
        s,
        errors="coerce",
        dayfirst=True
    )


def normalizar_id(serie: pd.Series) -> pd.Series:

    s = serie.astype("string").str.strip()

    s = s.str.replace(
        r"\.0$",
        "",
        regex=True
    )

    return s.replace({
        "": pd.NA,
        "nan": pd.NA,
        "None": pd.NA
    })


def normalizar_sexo(serie: pd.Series) -> pd.Series:

    return (
        serie.astype("string")
        .str.strip()
        .str.upper()
        .replace({
            "MASCULINO": "M",
            "FEMININO": "F"
        })
    )


# PREPARAÇÃO DAS BASES

def preparar_bases(
    ativos: pd.DataFrame,
    inativos: pd.DataFrame,
    pensionistas: pd.DataFrame
) -> pd.DataFrame:

    exigir_colunas(
        ativos,
        [
            "ID_FUNCIONAL",
            "DTNASC",
            "DTEXERC",
            "DTVAC",
            "FORMAVAC",
            "SEXO",
            "ORGAO_ORIGEM",
            "REGIMEJUR",
            "PLANO"
        ],
        "Ativos"
    )

    exigir_colunas(
        inativos,
        [
            "ID_FUNCIONAL",
            "DTNASC",
            "DTEXERC",
            "DTAPOSENT",
            "DTVAC",
            "FORMAVAC",
            "SEXO",
            "ORGAO_ORIGEM",
            "REGIMEJUR",
            "PLANO"
        ],
        "Inativos"
    )

    exigir_colunas(
        pensionistas,
        [
            "NUMFUNC",
            "DTNASC",
            "DT_INICIO_PENSAO",
            "DTVAC",
            "FORMAVAC",
            "SEXO",
            "ORGAO_ORIGEM",
            "REGIMEJUR",
            "PLANO"
        ],
        "Pensionistas"
    )

    # ATIVOS

    a = ativos.copy()

    a["DTAPOSENT"] = a["DTVAC"]
    a["DATA_INICIO"] = a["DTEXERC"]
    a["DATA_FIM"] = a["DTVAC"]

    a["CLASSE"] = "ATIVO"
    a["TIPO_BENEFICIO"] = "222"
    a["DS_PREFIXO"] = "111"

    # INATIVOS

    i = inativos.copy()

    i = i[
        i["DTAPOSENT"].notna()
        & i["DTAPOSENT"].astype("string").str.strip().ne("")
    ].copy()

    i["DATA_INICIO"] = i["DTAPOSENT"]
    i["DATA_FIM"] = i["DTVAC"]

    i["CLASSE"] = "INATIVO"

    if "TIPO_BENEFICIO" not in i.columns:

        i["TIPO_BENEFICIO"] = "222"

    else:

        i["TIPO_BENEFICIO"] = (
            i["TIPO_BENEFICIO"].fillna("222")
        )

    i["DS_PREFIXO"] = "111"

    # PENSIONISTAS

    p = pensionistas.copy()

    p = p.rename(
        columns={
            "NUMFUNC": "ID_FUNCIONAL",
            "DT_INICIO_PENSAO": "DTEXERC"
        }
    )

    p["DTAPOSENT"] = "31/12/2500"

    p["DATA_INICIO"] = p["DTEXERC"]
    p["DATA_FIM"] = p["DTVAC"]

    p["CLASSE"] = "PENSIONISTA"
    p["TIPO_BENEFICIO"] = "222"

    p["DS_PREFIXO"] = p.get(
        "ID_FUNCIONAL_INSTITUIDOR",
        pd.Series("", index=p.index)
    )

    # COLUNAS PADRONIZADAS

    cols = [
        "ID_FUNCIONAL",
        "DTNASC",
        "DTEXERC",
        "DTVAC",
        "FORMAVAC",
        "SEXO",
        "ORGAO_ORIGEM",
        "REGIMEJUR",
        "PLANO",
        "TIPO_BENEFICIO",
        "DTAPOSENT",
        "DS_PREFIXO",
        "DATA_FIM",
        "DATA_INICIO",
        "CLASSE"
    ]

    for frame in (a, i, p):

        frame["ID_FUNCIONAL"] = normalizar_id(
            frame["ID_FUNCIONAL"]
        )

    # POPULAÇÃO CIVIL

    a_civ = a[
        a["REGIMEJUR"]
        .astype("string")
        .str.strip()
        .str.upper()
        .ne("ESTATUTO MILITAR")
    ]

    i_civ = i[
        i["REGIMEJUR"]
        .astype("string")
        .str.strip()
        .str.upper()
        .ne("ESTATUTO MILITAR")
    ]

    civil = pd.concat(
        [
            x.reindex(columns=cols)
            for x in (a_civ, i_civ, p)
        ],
        ignore_index=True
    )

    civil = (
        civil
        .dropna(subset=["ID_FUNCIONAL"])
        .drop_duplicates(
            "ID_FUNCIONAL",
            keep="first"
        )
        .copy()
    )

    civil["POPULACAO"] = "CIVIL"

    # POPULAÇÃO MILITAR

    a_mil = a[
        a["REGIMEJUR"]
        .astype("string")
        .str.strip()
        .str.upper()
        .eq("ESTATUTO MILITAR")
    ]

    i_mil = i[
        i["REGIMEJUR"]
        .astype("string")
        .str.strip()
        .str.upper()
        .eq("ESTATUTO MILITAR")
    ]

    militar = pd.concat(
        [
            x.reindex(columns=cols)
            for x in (a_mil, i_mil)
        ],
        ignore_index=True
    )

    militar = (
        militar
        .dropna(subset=["ID_FUNCIONAL"])
        .drop_duplicates(
            "ID_FUNCIONAL",
            keep="first"
        )
        .copy()
    )

    militar["POPULACAO"] = "MILITAR"

    # BASE FINAL

    base = pd.concat(
        [civil, militar],
        ignore_index=True
    )

    for c in [
        "DTNASC",
        "DTEXERC",
        "DTVAC",
        "DTAPOSENT",
        "DATA_FIM",
        "DATA_INICIO"
    ]:

        base[c] = data_flexivel(base[c])

    form = (
        base["FORMAVAC"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    base["FORMAVAC"] = (
        form.mask(
            form.isna() | form.eq(""),
            "VIVO"
        )
    )

    base["SEXO"] = normalizar_sexo(
        base["SEXO"]
    )

    base["ORGAO_ORIGEM"] = (
        base["ORGAO_ORIGEM"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    base["REGIMEJUR"] = (
        base["REGIMEJUR"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    base["DATA_FIM"] = (
        base["DATA_FIM"]
        .fillna(pd.Timestamp("2200-01-01"))
    )

    return base


# PERÍODO DE OBSERVAÇÃO

def construir_observacao(
    base: pd.DataFrame,
    inicio: pd.Timestamp,
    fim: pd.Timestamp
) -> pd.DataFrame:

    if inicio > fim:

        raise ValueError(
            "A data inicial deve ser anterior ou igual à data final."
        )

    d = base.copy()

    d["Inicio_Obs"] = (
        d["DATA_INICIO"].clip(lower=inicio)
    )

    d["Final_Obs"] = (
        d["DATA_FIM"].clip(upper=fim)
    )

    d["Nao_Censura"] = (
        d["FORMAVAC"].eq("FALECIMENTO")
        & d["DATA_FIM"].between(
            inicio,
            fim,
            inclusive="both"
        )
    )

    d["Idade_no_Inicio"] = (
        (d["Inicio_Obs"] - d["DTNASC"]).dt.days
        / 365.25
    )

    d["Idade_no_Fim"] = (
        (d["Final_Obs"] - d["DTNASC"]).dt.days
        / 365.25
    )

    d = d[
        d["DTNASC"].notna()
        & d["Inicio_Obs"].notna()
        & d["Final_Obs"].notna()
    ]

    d = d[
        d["Idade_no_Fim"] <= 116
    ]

    d = d[
        (d["Final_Obs"] >= inicio)
        & (d["Inicio_Obs"] <= fim)
    ].copy()

    return d


# CÁLCULO DA EXPOSIÇÃO POR IDADE

def exposicao_por_idade_ano(
    df: pd.DataFrame,
    ano_inicio: pd.Timestamp,
    ano_fim: pd.Timestamp
) -> np.ndarray:

    inicio_ano = max(
        ano_inicio,
        pd.Timestamp(ano_inicio.year, 1, 1)
    )

    fim_ano = min(
        ano_fim,
        pd.Timestamp(ano_inicio.year, 12, 31)
    )

    if inicio_ano > fim_ano or df.empty:

        return np.zeros(
            MAX_AGE + 1,
            dtype=float
        )

    ini = df["Inicio_Obs"].clip(
        lower=inicio_ano,
        upper=fim_ano
    )

    fim_individual = df["Final_Obs"].where(
        df["Nao_Censura"],
        fim_ano
    )

    fim_individual = fim_individual.clip(
        lower=inicio_ano,
        upper=fim_ano
    )

    valid = (
        ini.notna()
        & fim_individual.notna()
        & (ini <= fim_individual)
    )

    if not valid.any():

        return np.zeros(
            MAX_AGE + 1,
            dtype=float
        )

    sub = df.loc[valid]

    idade_ini = (
        (ini.loc[valid] - sub["DTNASC"])
        .dt.days.to_numpy(dtype=float)
        / 365.25
    )

    idade_fim = (
        (fim_individual.loc[valid] - sub["DTNASC"])
        .dt.days.to_numpy(dtype=float)
        / 365.25
    )

    exp = np.zeros(
        MAX_AGE + 1,
        dtype=float
    )

    for x in range(MAX_AGE + 1):

        # Permanece na mesma idade.
        mesma = (
            (np.floor(idade_ini) == x)
            & (np.floor(idade_fim) == x)
        )

        exp[x] += np.maximum(
            idade_fim[mesma] - idade_ini[mesma],
            0
        ).sum()

        # Começa na idade x e atravessa para x+1.
        atravessa = (
            (np.floor(idade_ini) == x)
            & (np.floor(idade_fim) == x + 1)
        )

        exp[x] += np.maximum(
            (x + 1) - idade_ini[atravessa],
            0
        ).sum()

        # Começa na idade x-1 e termina na idade x.
        termina = (
            (np.floor(idade_ini) == x - 1)
            & (np.floor(idade_fim) == x)
        )

        exp[x] += np.maximum(
            idade_fim[termina] - x,
            0
        ).sum()

    return exp


# LEITURA DAS TÁBUAS

def ler_tabuas(upload) -> pd.DataFrame:

    t = ler_csv(
        upload,
        "Tábuas de mortalidade"
    )

    mapa = {
        c: c.strip()
        for c in t.columns
    }

    t = t.rename(columns=mapa)

    col_idade = next(
        (
            c for c in t.columns
            if c.lower() in ("idade", "idade.x")
        ),
        None
    )

    if col_idade is None:

        raise ValueError(
            "A tabela de tábuas precisa ter uma coluna 'idade'."
        )

    t = t.rename(
        columns={
            col_idade: "idade"
        }
    )

    t["idade"] = pd.to_numeric(
        t["idade"].astype(str).str.replace(",", "."),
        errors="coerce"
    )

    for c in t.columns:

        if c == "idade":
            continue

        s = (
            t[c]
            .astype("string")
            .str.strip()
        )

        tem_virgula = s.str.contains(
            ",",
            na=False
        )

        s = s.where(
            ~tem_virgula,
            s.str.replace(".", "", regex=False)
             .str.replace(",", ".", regex=False)
        )

        t[c] = pd.to_numeric(
            s,
            errors="coerce"
        )

    t = (
        t.dropna(subset=["idade"])
        .drop_duplicates("idade")
        .set_index("idade")
        .reindex(range(MAX_AGE + 1))
    )

    return t


# CÁLCULO DE OBSERVADOS, EXPOSTOS E ESPERADOS

def calcular_grupo(
    df: pd.DataFrame,
    tabuas: pd.DataFrame,
    coluna_tabua: str,
    inicio: pd.Timestamp,
    fim: pd.Timestamp
):

    if coluna_tabua not in tabuas.columns:

        raise ValueError(
            f"A coluna de tábua '{coluna_tabua}' "
            "não foi encontrada no CSV."
        )

    # EXPOSIÇÃO

    exposicao = np.zeros(
        MAX_AGE + 1,
        dtype=float
    )

    for ano in range(
        inicio.year,
        fim.year + 1
    ):

        ini_ano = max(
            inicio,
            pd.Timestamp(ano, 1, 1)
        )

        fim_ano = min(
            fim,
            pd.Timestamp(ano, 12, 31)
        )

        exposicao += exposicao_por_idade_ano(
            df,
            ini_ano,
            fim_ano
        )

    # OBSERVADOS

    obitos = np.zeros(
        MAX_AGE + 1,
        dtype=float
    )

    mortos = df[
        df["Nao_Censura"]
    ].copy()

    if not mortos.empty:

        idade_obito = np.floor(
            mortos["Idade_no_Fim"]
        ).astype(int)

        contagem = idade_obito.value_counts()

        for idade, quantidade in contagem.items():

            if 0 <= idade <= MAX_AGE:

                obitos[idade] = quantidade

    # ESPERADOS

    qx = tabuas[coluna_tabua].to_numpy(
        dtype=float
    )

    qx = np.nan_to_num(
        qx,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    qx = np.clip(
        qx,
        0,
        1
    )

    esperados = exposicao * qx

    # TABELA FINAL

    resultado = pd.DataFrame({

        "Idade": np.arange(
            MAX_AGE + 1
        ),

        "Observados": obitos,

        "Expostos": exposicao,

        "Esperados": esperados

    })

    total_obs = float(
        obitos.sum()
    )

    total_esp = float(
        esperados.sum()
    )

    resumo = {

        "Óbitos observados": total_obs,

        "Óbitos esperados": total_esp,

        "Razão O/E": (
            total_obs / total_esp
            if total_esp > 0
            else np.nan
        )

    }

    return resultado, resumo

# CONTROLE DO BOTÃO LIMPAR TUDO

if "limpeza_uploads" not in st.session_state:
    st.session_state["limpeza_uploads"] = 0


def limpar_tudo():
    # Gera novas chaves para limpar os arquivos carregados
    st.session_state["limpeza_uploads"] += 1

    # Restaura as datas
    st.session_state["dt_inicio"] = date(2019, 1, 1)
    st.session_state["dt_fim"] = date(2023, 12, 31)

# INTERFACE

with st.sidebar:

    st.header("📂 Arquivos de entrada")

    up_ativos = st.file_uploader(
        "Ativos.csv",
        type="csv",
        key=f"ativos_{st.session_state['limpeza_uploads']}"
    )

    up_inativos = st.file_uploader(
        "Inativos.csv",
        type="csv",
        key=f"inativos_{st.session_state['limpeza_uploads']}"
    )

    up_pens = st.file_uploader(
        "Pensionistas.csv",
        type="csv",
        key=f"pensionistas_{st.session_state['limpeza_uploads']}"
    )

    up_tabuas = st.file_uploader(
        "Tábuas de mortalidade.csv",
        type="csv",
        key=f"tabuas_{st.session_state['limpeza_uploads']}"
    )

    st.divider()

    st.header("📅 Período de observação")

    col_ini, col_fim = st.columns(2)

    with col_ini:
        dt_inicio = st.date_input(
            "Data Inicial",
            value=date(2019, 1, 1),
            format="DD/MM/YYYY",
            key="dt_inicio"
        )

    with col_fim:
        dt_fim = st.date_input(
            "Data Final",
            value=date(2023, 12, 31),
            format="DD/MM/YYYY",
            key="dt_fim"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    executar = st.button(
        "🚀 Executar auditoria",
        type="primary",
        use_container_width=True
    )

    st.button(
        "🧹 Limpar tudo",
        use_container_width=True,
        on_click=limpar_tudo
    )


# EXECUÇÃO

if executar:

    if not all([
        up_ativos,
        up_inativos,
        up_pens,
        up_tabuas
    ]):

        st.error(
            "⚠️ Envie os quatro arquivos obrigatórios: "
            "Ativos, Inativos, Pensionistas e Tábuas."
        )

    elif not dt_inicio or not dt_fim:

        st.error(
            "⚠️ Selecione a data inicial e a data final do período."
        )

    elif dt_inicio > dt_fim:

        st.error(
            "⚠️ A data inicial não pode ser posterior à data final."
        )

    else:

        try:

            inicio = pd.Timestamp(dt_inicio)
            fim = pd.Timestamp(dt_fim)

            with st.spinner(
                "Lendo bases e calculando exposição e óbitos esperados..."
            ):

                ativos = ler_csv(
                    up_ativos,
                    "Ativos"
                )

                inativos = ler_csv(
                    up_inativos,
                    "Inativos"
                )

                pensionistas = ler_csv(
                    up_pens,
                    "Pensionistas"
                )

                tabuas = ler_tabuas(
                    up_tabuas
                )

                base = preparar_bases(
                    ativos,
                    inativos,
                    pensionistas
                )

                obs = construir_observacao(
                    base,
                    inicio,
                    fim
                )

                # SEPARAÇÃO DAS POPULAÇÕES

                civis = obs[
                    obs["POPULACAO"].eq("CIVIL")
                ].copy()

                militares = obs[
                    obs["POPULACAO"].eq("MILITAR")
                ].copy()


                grupos = {

                    "Civil_Masculino": (
                        civis[
                            civis["SEXO"].eq("M")
                        ],
                        "Tabua_Mort_Civil_Masculino_UP_94_M_mais8"
                    ),

                    "Civil_Feminino": (
                        civis[
                            civis["SEXO"].eq("F")
                        ],
                        "Tabua_Mort_Civil_Feminino_SGB_71_menos74"
                    ),

                    "PMERJ": (
                        militares[
                            militares["ORGAO_ORIGEM"].eq("SEPM")
                        ],
                        "Tabua_Mort_PMERJ_AT_55"
                    ),

                    "CBMERJ": (
                        militares[
                            militares["ORGAO_ORIGEM"].eq("SEDEC")
                        ],
                        "Tabua_Mort_CBMERJ_UP_94_M_mais6"
                    )

                }


                resultados = {}
                resumos = {}

                for nome, (df_grupo, coluna) in grupos.items():

                    resultados[nome], resumos[nome] = calcular_grupo(
                        df_grupo,
                        tabuas,
                        coluna,
                        inicio,
                        fim
                    )

            # RESULTADO GERAL

            st.success(
                f"✨ Auditoria concluída com sucesso: "
                f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}."
            )

            st.markdown("<br>", unsafe_allow_html=True)
            
            # QUADROS (MÉTRICAS) EM CIMÁ
            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "👥 Segurados na observação",
                    f"{len(obs):,}".replace(",", ".")
                )

            with c2:
                st.metric(
                    "✝️ Óbitos observados",
                    f"{sum(x['Óbitos observados'] for x in resumos.values()):,.0f}".replace(",", ".")
                )

            with c3:
                val_esp = sum(x['Óbitos esperados'] for x in resumos.values())
                val_esp_fmt = f"{val_esp:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                st.metric(
                    "📈 Óbitos esperados",
                    val_esp_fmt
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # RESUMO EXECUTIVO LOGO ABAIXO DOS QUADROS
            resumo_df = (
                pd.DataFrame(resumos)
                .T
                .reset_index(names="Grupo")
            )

            st.markdown("📋 Resumo Executivo por Grupo")

            st.dataframe(
                resumo_df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("<br>", unsafe_allow_html=True)
            st.divider()

            # TABELAS E GRÁFICO

            st.markdown("📊 Detalhamento por Segmento Atuarial")
            tabs = st.tabs(list(resultados.keys()))

            for tab, (nome, tabela) in zip(tabs, resultados.items()):

                with tab:

                    st.markdown(f"🔎 Segmento: {nome.replace('_', ' ')}")

                    # Tabela
                    st.dataframe(
                        tabela[
                            ["Idade", "Observados", "Expostos", "Esperados"]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # gráfico observados x esperados
                    st.markdown("📈 Curva Comparativa: Óbitos Observados vs. Esperados por Idade")

                    grafico_obitos = (
                        tabela
                        .set_index("Idade")[["Observados", "Esperados"]]
                    )

                    st.line_chart(
                        grafico_obitos,
                        x_label="Idade",
                        y_label="Quantidade de óbitos"
                    )
            
            st.divider()

            # EXPORTAÇÃO PARA EXCEL

            st.markdown("💾 Exportação de Relatórios")

            output = io.BytesIO()

            with pd.ExcelWriter(
                output,
                engine="xlsxwriter"
            ) as writer:

                resumo_df.to_excel(
                    writer,
                    sheet_name="Resumo",
                    index=False
                )

                for nome, tabela in resultados.items():

                    tabela[
                        [
                            "Idade",
                            "Observados",
                            "Expostos",
                            "Esperados"
                        ]
                    ].to_excel(
                        writer,
                        sheet_name=nome[:31],
                        index=False
                    )

                
            st.download_buffer = output.getvalue()

            st.download_button("📥 Baixar auditoria completa em Excel",

                data=output.getvalue(),

                file_name=(
                    f"Auditoria_Tabuas_"
                    f"{inicio:%Y%m%d}_{fim:%Y%m%d}.xlsx"
                ),

                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),

                use_container_width=True,

                on_click="ignore"
            )

        except Exception as exc:

            st.exception(exc)

else:

    st.markdown("""
        <div style="padding: 20px; border-radius: 10px; background-color: #1f2937; border: 1px solid #374151; text-align: center;">
            <h3 style="color: #f3f4f6; margin-bottom: 10px;">👋 Bem-vindo à Ferramenta de Auditoria Atuarial</h3>
            <p style="color: #9ca3af; font-size: 16px;">
                Na barra lateral à esquerda, carregue os arquivos <b>Ativos.csv</b>, <b>Inativos.csv</b>, <b>Pensionistas.csv</b> e o arquivo de <b>Tábuas de mortalidade.csv</b>. 
                Em seguida, selecione o período desejado e clique em <b>Executar auditoria</b> para gerar os relatórios e gráficos analíticos.
            </p>
        </div>
    """, unsafe_allow_html=True)