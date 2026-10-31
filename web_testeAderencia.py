import io
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Auditoria de Tábuas Biométricas",
    page_icon="📊",
    layout="wide",
)

# Estilização CSS personalizada para uniformizar os botões
st.markdown("""
    <style>
        .stButton > button {
            width: 100%;
            border-radius: 6px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Auditoria de Aderência de Tábuas Biométricas")
st.markdown(
    "Ferramenta desenvolvida para Análise de Dados,"
    " processamento, limpeza, cálculo de expostos ao risco e auditoria de"
    " mortalidade do Rioprevidência."
)

st.markdown("---")

if "executado" not in st.session_state:
  st.session_state.executado = False

st.sidebar.header("📝 Upload de arquivos e seleção de datas")
st.sidebar.markdown("*Faça o upload dos arquivos CSV abaixo:*")

uploaded_ativos = st.sidebar.file_uploader(
    "📂 Ativos (.csv)", type=["csv"], help="Arraste ou selecione o arquivo de Ativos"
)
uploaded_inativos = st.sidebar.file_uploader(
    "📂 Inativos (.csv)", type=["csv"], help="Arraste ou selecione o arquivo de Inativos"
)
uploaded_pensionistas = st.sidebar.file_uploader(
    "📂 Pensionistas (.csv)", type=["csv"], help="Arraste ou selecione o arquivo de Pensionistas"
)

st.sidebar.markdown("---")
st.sidebar.header("📅 Período de Observação")

data_inicio_obs = st.sidebar.date_input(
    "Data de Início", 
    value=pd.to_datetime("2019-01-01"),
    format="DD/MM/YYYY"
)
data_data_fim_obs = st.sidebar.date_input(
    "Data de Término", 
    value=pd.to_datetime("2023-12-31"),
    format="DD/MM/YYYY"
)

data_inicio_obs = pd.to_datetime(data_inicio_obs)
data_final_obs = pd.to_datetime(data_data_fim_obs)

TABUA_PATH = "Tabuas_Mortalidade_Geral Civil e Militar.csv"

st.sidebar.markdown("---")
col_btn1, col_btn2 = st.sidebar.columns(2)
executar = col_btn1.button("🚀 Executar", type="primary")
limpar = col_btn2.button("🧹 Limpar")

if limpar:
  st.session_state.executado = False
  st.rerun()

if executar or st.session_state.executado:
  if not uploaded_ativos or not uploaded_inativos or not uploaded_pensionistas:
    st.error(
        "⚠️ Por favor, faça o upload dos três arquivos (Ativos, Inativos e"
        " Pensionistas) no menu lateral para continuar."
    )
  else:
    st.session_state.executado = True
    with st.spinner(
        "Processando ETL, limpeza, segregação e cálculos de exposição..."
        " Aguarde."
    ):
      try:
        tabuas_mortalidade = pd.read_csv(TABUA_PATH, sep=";", encoding="latin1")
        ativos = pd.read_csv(uploaded_ativos, sep=";", encoding="latin1")
        inativos = pd.read_csv(uploaded_inativos, sep=";", encoding="latin1")
        pensionistas = pd.read_csv(
            uploaded_pensionistas, sep=";", encoding="latin1", low_memory=False
        )

        ativos["DTNASC"] = pd.to_datetime(
            ativos["DTNASC"], format="%d/%m/%Y", errors="coerce"
        )
        ativos["DTEXERC"] = pd.to_datetime(
            ativos["DTEXERC"], format="%d/%m/%Y", errors="coerce"
        )
        ativos["DTVAC"] = pd.to_datetime(
            ativos["DTVAC"], format="%d/%m/%Y", errors="coerce"
        )
        ativos["DTVAC"] = ativos["DTVAC"].fillna(pd.to_datetime("2200-01-01"))
        ativos["FORMAVAC"] = (
            ativos["FORMAVAC"].fillna("VIVO").replace("", "VIVO")
        )
        ativos["TIPO_BENEFICIO"] = 222
        ativos["DTAPOSENT"] = ativos["DTVAC"]
        ativos["DS_PREFIXO"] = 111
        ativos["DATA_FIM"] = ativos["DTVAC"]
        ativos["DATA_INICIO"] = ativos["DTEXERC"]
        ativos["CLASSE"] = "ATIVO"

        inativos["ID_FUNCIONAL"] = inativos["ID_FUNCIONAL"].astype(str)
        inativos["DTNASC"] = pd.to_datetime(
            inativos["DTNASC"], format="%d/%m/%Y", errors="coerce"
        )
        inativos["DTEXERC"] = pd.to_datetime(
            inativos["DTEXERC"], format="%d/%m/%Y", errors="coerce"
        )
        inativos["DTAPOSENT"] = pd.to_datetime(
            inativos["DTAPOSENT"], format="%d/%m/%Y", errors="coerce"
        )
        inativos["DTVAC"] = pd.to_datetime(
            inativos["DTVAC"], format="%d/%m/%Y", errors="coerce"
        )
        inativos["DTVAC"] = inativos["DTVAC"].fillna(
            pd.to_datetime("2200-01-01")
        )
        inativos["FORMAVAC"] = (
            inativos["FORMAVAC"].fillna("VIVO").replace("", "VIVO")
        )
        inativos = inativos.dropna(subset=["DTAPOSENT"])
        inativos["TIPO_BENEFICIO"] = inativos["TIPO_BENEFICIO"].fillna(222)
        inativos["DS_PREFIXO"] = 111
        inativos["DATA_FIM"] = inativos["DTVAC"]
        inativos["DATA_INICIO"] = inativos["DTAPOSENT"]
        inativos["CLASSE"] = "INATIVO"

        pensionistas["DTNASC"] = pd.to_datetime(
            pensionistas["DTNASC"], format="%d/%m/%Y", errors="coerce"
        )
        pensionistas["DT_INICIO_PENSAO"] = pd.to_datetime(
            pensionistas["DT_INICIO_PENSAO"],
            format="%d/%m/%Y",
            errors="coerce",
        )
        pensionistas["DTVAC"] = pd.to_datetime(
            pensionistas["DTVAC"], format="%d/%m/%Y", errors="coerce"
        )
        pensionistas["DTVAC"] = pensionistas["DTVAC"].fillna(
            pd.to_datetime("2200-01-01")
        )
        pensionistas["FORMAVAC"] = (
            pensionistas["FORMAVAC"].fillna("VIVO").replace("", "VIVO")
        )
        pensionistas["FORMAVAC"] = pensionistas["FORMAVAC"].replace(
            "Falecimento", "FALECIMENTO"
        )
        pensionistas["ID_FUNCIONAL_INSTITUIDOR"] = pd.to_numeric(
            pensionistas["ID_FUNCIONAL_INSTITUIDOR"], errors="coerce"
        )
        pensionistas["DS_PREFIXO"] = pensionistas["ID_FUNCIONAL_INSTITUIDOR"]
        pensionistas["DTAPOSENT"] = pd.to_datetime(
            "2200-12-31", format="%Y-%m-%d"
        )
        pensionistas["TIPO_BENEFICIO"] = 222
        pensionistas["DATA_FIM"] = pensionistas["DTVAC"]
        pensionistas["DATA_INICIO"] = pensionistas["DT_INICIO_PENSAO"]
        pensionistas["CLASSE"] = "PENSIONISTA"

        colunas_padrao = [
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
            "CLASSE",
        ]
        pensionistas_mod = pensionistas.rename(
            columns={
                "NUMFUNC": "ID_FUNCIONAL",
                "DT_INICIO_PENSAO": "DTEXERC",
            }
        )

        dados_gerais = pd.concat(
            [
                ativos[colunas_padrao],
                inativos[colunas_padrao],
                pensionistas_mod[colunas_padrao],
            ],
            ignore_index=True,
        )

        dados_gerais = dados_gerais.drop_duplicates(
            subset=["ID_FUNCIONAL"], keep="first"
        )

        dados_gerais["Inicio_Obs"] = dados_gerais["DATA_INICIO"].clip(
            lower=data_inicio_obs
        )
        dados_gerais["Final_Obs"] = dados_gerais["DATA_FIM"].clip(
            upper=data_final_obs
        )

        cond_nao_censura = (
            (dados_gerais["FORMAVAC"] == "FALECIMENTO")
            & (dados_gerais["DATA_FIM"] <= data_final_obs)
            & (dados_gerais["DATA_FIM"] >= data_inicio_obs)
        )
        dados_gerais["Nao_Censura"] = cond_nao_censura

        dados_gerais["Idade_no_Inicio"] = (
            dados_gerais["Inicio_Obs"] - dados_gerais["DTNASC"]
        ).dt.days / 365.25
        dados_gerais["Idade_no_Fim"] = (
            dados_gerais["Final_Obs"] - dados_gerais["DTNASC"]
        ).dt.days / 365.25
        dados_gerais = dados_gerais[dados_gerais["Idade_no_Fim"] <= 116]

        dados_gerais_obs = dados_gerais[
            (dados_gerais["Final_Obs"] >= data_inicio_obs)
            & (dados_gerais["Inicio_Obs"] <= data_final_obs)
        ].copy()

        dados_gerais_obs["Idade_no_Inicio"] = (
            dados_gerais_obs["Inicio_Obs"] - dados_gerais_obs["DTNASC"]
        ).dt.days / 365.25
        dados_gerais_obs["Idade_no_Fim"] = (
            dados_gerais_obs["Final_Obs"] - dados_gerais_obs["DTNASC"]
        ).dt.days / 365.25

        # Segregação
        df_civis_m = dados_gerais_obs[
            (dados_gerais_obs["REGIMEJUR"] != "ESTATUTO MILITAR")
            & (dados_gerais_obs["SEXO"] == "M")
        ].copy()
        df_civis_f = dados_gerais_obs[
            (dados_gerais_obs["REGIMEJUR"] != "ESTATUTO MILITAR")
            & (dados_gerais_obs["SEXO"] == "F")
        ].copy()

        df_pm_m = dados_gerais_obs[
            (dados_gerais_obs["ORGAO_ORIGEM"] == "SEPM")
            & (dados_gerais_obs["SEXO"] == "M")
        ].copy()
        df_pm_f = dados_gerais_obs[
            (dados_gerais_obs["ORGAO_ORIGEM"] == "SEPM")
            & (dados_gerais_obs["SEXO"] == "F")
        ].copy()

        df_cb_m = dados_gerais_obs[
            (dados_gerais_obs["ORGAO_ORIGEM"] == "SEDEC")
            & (dados_gerais_obs["SEXO"] == "M")
        ].copy()
        df_cb_f = dados_gerais_obs[
            (dados_gerais_obs["ORGAO_ORIGEM"] == "SEDEC")
            & (dados_gerais_obs["SEXO"] == "F")
        ].copy()

        for col in tabuas_mortalidade.columns:
          if col != "idade":
            if tabuas_mortalidade[col].dtype == object:
              tabuas_mortalidade[col] = (
                  tabuas_mortalidade[col]
                  .astype(str)
                  .str.replace(",", ".")
                  .astype(float)
              )

        ano_inicio_int = data_inicio_obs.year
        ano_fim_int = data_final_obs.year
        anos_estudo = range(ano_inicio_int, ano_fim_int + 1)

        datas_inicio_anos = pd.to_datetime(
            [f"{a}-01-01" for a in anos_estudo]
        )
        datas_fim_anos = pd.to_datetime([f"{a}-12-31" for a in anos_estudo])

        def processar_aderencia_sexo(df_obs, tabuas_df, nome_coluna_tabua):
          saidas_obs = df_obs[df_obs["Nao_Censura"] == True].copy()
          max_idade = 126

          num_obitos_df = pd.DataFrame({"IDADE": range(max_idade + 1)})
          for ano in anos_estudo:
            num_obitos_df[str(ano)] = 0

          saidas_obs["Idade_Inteira_Obito"] = np.floor(
              saidas_obs["Idade_no_Fim"]
          ).astype(int)

          for idade in range(max_idade + 1):
            for idx, ano in enumerate(anos_estudo):
              d_ini = datas_inicio_anos[idx]
              d_fim = datas_fim_anos[idx]
              contagem = len(
                  saidas_obs[
                      (saidas_obs["Idade_Inteira_Obito"] == idade)
                      & (saidas_obs["DATA_FIM"] >= d_ini)
                      & (saidas_obs["DATA_FIM"] <= d_fim)
                  ]
              )
              num_obitos_df.loc[num_obitos_df["IDADE"] == idade, str(ano)] = (
                  contagem
              )

          num_obitos_df["TOTAL"] = num_obitos_df[
              [str(a) for a in anos_estudo]
          ].sum(axis=1)

          num_expostos_df = pd.DataFrame({"IDADE": range(max_idade + 1)})
          for ano in anos_estudo:
            num_expostos_df[str(ano)] = 0.0

          for idx, ano in enumerate(anos_estudo):
            d_ini = datas_inicio_anos[idx]
            d_fim = datas_fim_anos[idx]
            obs_ini = df_obs["Inicio_Obs"].clip(lower=d_ini, upper=d_fim)
            obs_fim = df_obs["Final_Obs"].clip(lower=d_ini, upper=d_fim)
            valid = obs_ini <= obs_fim
            if not valid.any():
              continue
            sub = df_obs[valid].copy()
            anos_exp = (obs_fim[valid] - obs_ini[valid]).dt.days / 365.25
            sub["_exp_ano"] = anos_exp
            sub["_idade_int"] = np.floor(sub["Idade_no_Inicio"]).astype(int)
            exp_por_idade = sub.groupby("_idade_int")["_exp_ano"].sum()
            for idade in range(max_idade + 1):
              if idade in exp_por_idade:
                num_expostos_df.loc[
                    num_expostos_df["IDADE"] == idade, str(ano)
                ] = exp_por_idade[idade]

          num_expostos_df["TOTAL"] = num_expostos_df[
              [str(a) for a in anos_estudo]
          ].sum(axis=1)

          tabela_auditoria = pd.DataFrame({"IDADE": range(max_idade + 1)})
          tabela_auditoria["Observados"] = num_obitos_df["TOTAL"]
          tabela_auditoria["Expostos"] = num_expostos_df["TOTAL"]

          prob_qx = (
              tabuas_df.set_index("idade")[nome_coluna_tabua]
              .reindex(range(max_idade + 1))
              .fillna(0)
              .values
          )
          tabela_auditoria["Esperados"] = (
              tabela_auditoria["Expostos"] * prob_qx
          )

          return tabela_auditoria

        auditoria_civis_m = processar_aderencia_sexo(
            df_civis_m,
            tabuas_mortalidade,
            "Tabua_Mort_Civil_Masculino_UP_94_M_mais8",
        )
        auditoria_civis_f = processar_aderencia_sexo(
            df_civis_f,
            tabuas_mortalidade,
            "Tabua_Mort_Civil_Feminino_SGB_71_menos74",
        )

        auditoria_pm_m = processar_aderencia_sexo(
            df_pm_m, tabuas_mortalidade, "Tabua_Mort_PMERJ_AT_55"
        )
        auditoria_pm_f = processar_aderencia_sexo(
            df_pm_f, tabuas_mortalidade, "Tabua_Mort_PMERJ_AT_55"
        )

        auditoria_cb_m = processar_aderencia_sexo(
            df_cb_m, tabuas_mortalidade, "Tabua_Mort_CBMERJ_UP_94_M_mais6"
        )
        auditoria_cb_f = processar_aderencia_sexo(
            df_cb_f, tabuas_mortalidade, "Tabua_Mort_CBMERJ_UP_94_M_mais6"
        )

        st.success(
            f"✅ Auditoria executada com sucesso para o período de"
            f" {data_inicio_obs.strftime('%d/%m/%Y')} a"
            f" {data_final_obs.strftime('%d/%m/%Y')}!"
        )

        # Totais de Óbitos por Categoria
        obitos_civis = auditoria_civis_m['Observados'].sum() + auditoria_civis_f['Observados'].sum()
        obitos_pm = auditoria_pm_m['Observados'].sum() + auditoria_pm_f['Observados'].sum()
        obitos_cb = auditoria_cb_m['Observados'].sum() + auditoria_cb_f['Observados'].sum()
        total_obitos = obitos_civis + obitos_pm + obitos_cb

        # Blocos de Métricas Superiores Organizados
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Total Segurados", f"{len(dados_gerais_obs):,}".replace(",", "."))
        col2.metric("✝️ Total Óbitos Gerais", f"{total_obitos:,.0f}".replace(",", "."))
        col3.metric("👮 Óbitos PMERJ", f"{obitos_pm:,.0f}".replace(",", "."))
        col4.metric("🚒 Óbitos CBMERJ", f"{obitos_cb:,.0f}".replace(",", "."))

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs([
            "🏛️ Civis",
            "👮 Polícia Militar (SEPM)",
            "🚒 Bombeiros (SEDEC)",
        ])

        with tab1:
          col_m, col_f = st.columns(2)
          with col_m:
            st.subheader("Civis - Masculino")
            st.dataframe(auditoria_civis_m, use_container_width=True)
            st.line_chart(
                auditoria_civis_m.set_index("IDADE")[["Observados", "Esperados"]]
            )
          with col_f:
            st.subheader("Civis - Feminino")
            st.dataframe(auditoria_civis_f, use_container_width=True)
            st.line_chart(
                auditoria_civis_f.set_index("IDADE")[["Observados", "Esperados"]]
            )

        with tab2:
          col_m, col_f = st.columns(2)
          with col_m:
            st.subheader("PMERJ - Masculino")
            st.dataframe(auditoria_pm_m, use_container_width=True)
            st.line_chart(
                auditoria_pm_m.set_index("IDADE")[["Observados", "Esperados"]]
            )
          with col_f:
            st.subheader("PMERJ - Feminino")
            st.dataframe(auditoria_pm_f, use_container_width=True)
            st.line_chart(
                auditoria_pm_f.set_index("IDADE")[["Observados", "Esperados"]]
            )

        with tab3:
          col_m, col_f = st.columns(2)
          with col_m:
            st.subheader("CBMERJ - Masculino")
            st.dataframe(auditoria_cb_m, use_container_width=True)
            st.line_chart(
                auditoria_cb_m.set_index("IDADE")[["Observados", "Esperados"]]
            )
          with col_f:
            st.subheader("CBMERJ - Feminino")
            st.dataframe(auditoria_cb_f, use_container_width=True)
            st.line_chart(
                auditoria_cb_f.set_index("IDADE")[["Observados", "Esperados"]]
            )

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
          auditoria_civis_m.to_excel(
              writer, sheet_name="Civis_Masculino", index=False
          )
          auditoria_civis_f.to_excel(
              writer, sheet_name="Civis_Feminino", index=False
          )
          auditoria_pm_m.to_excel(
              writer, sheet_name="PMERJ_Masculino", index=False
          )
          auditoria_pm_f.to_excel(
              writer, sheet_name="PMERJ_Feminino", index=False
          )
          auditoria_cb_m.to_excel(
              writer, sheet_name="CBMERJ_Masculino", index=False
          )
          auditoria_cb_f.to_excel(
              writer, sheet_name="CBMERJ_Feminino", index=False
          )
        excel_data = output.getvalue()

        st.download_button(
            label="📥 Baixar Relatório Completo em Excel",
            data=excel_data,
            file_name=(
                f"Resultados_Auditoria_{data_inicio_obs.year}_{data_final_obs.year}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )

      except Exception as e:
        st.error(f"❌ Ocorreu um erro durante o processamento: {e}")
else:
  st.info(
      "👈 **Para começar:** Selecione os arquivos e defina o período de"
      " observação na barra lateral à esquerda, depois clique em **Executar**."
  )