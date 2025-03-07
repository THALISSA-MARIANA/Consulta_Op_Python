import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
load_dotenv()

def connect_to_sql_server():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(connection_string)


# Função para buscar dados filtrados no banco de dados
def fetch_filtered_data(op_number):
    query = f"""
    SELECT 
        'PAI' AS tipo_pai,
        SC2.C2_NUM AS ordem_producao,
        SG1.G1_COMP AS produto_pai,
        

        'Filho' AS tipo_filho,
        SG1.G1_COMP AS codigo_componente,
        SB1.B1_DESC AS descricao_produto,
        SB1.B1_TIPO AS tipo_produto,
        SB1.B1_UM AS unidade,
        SB1.B1_GRUPO AS grupo,
        SB2.B2_SALPEDI AS ops_colocadas,
        SB2.B2_QATU AS quantidade_atual,
        SB2.B2_QEMP AS quantidade_empenho,
        (ISNULL(Sub.C7_QUANT, 0) - ISNULL(Sub.C7_QUJE, 0)) AS pcs_colocados,
        (ISNULL(SB2.B2_QATU, 0) - ISNULL(SB2.B2_QEMP, 0)) AS disponivel
    FROM 
        Protheus_Pro.dbo.SG1000 AS SG1
    INNER JOIN 
        Protheus_Pro.dbo.SB1000 AS SB1 ON SG1.G1_COMP = SB1.B1_COD
    INNER JOIN 
        Protheus_Pro.dbo.SB2000 AS SB2 ON SG1.G1_COMP = SB2.B2_COD
    LEFT JOIN
        Protheus_Pro.dbo.SC6000 AS SC6 ON SG1.G1_COD = SC6.C6_PRODUTO
    LEFT JOIN
        Protheus_Pro.dbo.SC7000 AS SC7 ON SG1.G1_COD = SC7.C7_PRODUTO
    LEFT JOIN 
        Protheus_Pro.dbo.SC2000 AS SC2 ON SG1.G1_COD = SC2.C2_PRODUTO
    LEFT JOIN 
        (
            SELECT 
                C7_PRODUTO,
                C7_NUM,
                ISNULL(C7_QUANT, 0) AS C7_QUANT,
                ISNULL(C7_QUJE, 0) AS C7_QUJE
            FROM 
                Protheus_Pro.dbo.SC7000
        ) AS Sub ON SC7.C7_PRODUTO = Sub.C7_PRODUTO AND SC7.C7_NUM = Sub.C7_NUM
    WHERE 
        SC2.C2_NUM = ?
    ORDER BY 
        SC2.C2_PRODUTO;
    """
    conn = connect_to_sql_server()
    data = pd.read_sql(query, conn, params=[op_number])
    conn.close()
    return data

# Interface Streamlit
st.title("Consulta de Ordem de Produção")

# Campo para entrada da OP
op_number = st.text_input("Digite o número da Ordem de Produção (OP):")

if op_number:
    try:
        # Busca os dados filtrados
        df = fetch_filtered_data(op_number)
        
        if not df.empty:
            st.success(f"Resultados encontrados para OP: {op_number}")
            st.dataframe(df)  # Exibe os dados em uma tabela
            # Botão para exportar para Excel
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar como CSV",
                data=csv,
                file_name=f"op_{op_number}.csv",
                mime="text/csv",
            )
        else:
            st.warning("Nenhum dado encontrado para a OP fornecida.")
    except Exception as e:
        st.error(f"Erro ao buscar os dados: {e}")
