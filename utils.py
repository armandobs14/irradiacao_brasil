import pymysql
import requests
from datetime import datetime

# Recuperar conexão com banco
def pegar_conexao():
    return pymysql.connect(host='mysql', user='root', passwd='password')

# Função para criar banco de dados
def criar_banco():
    """
    Criação do banco de dados
    ===
    """
    conexao = pegar_conexao()
    
    # Cria um cursor:
    cursor = conexao.cursor()

    # Cria Banco e tabelas
    try:
        
        cursor.execute("CREATE SCHEMA IF NOT EXISTS `nasa_solarview`")

        cursor.execute("""CREATE TABLE `nasa_solarview`.`point` (
                          `id` INT NOT NULL AUTO_INCREMENT,
                          `pt` POINT NOT NULL,
                          `alt` DOUBLE NOT NULL,
                          PRIMARY KEY (`id`));
                        """)

        cursor.execute("""CREATE TABLE `nasa_solarview`.`irradiacao` (
                          `id` INT NOT NULL AUTO_INCREMENT,
                          `point_id` INT NOT NULL,
                          `date` DATE NOT NULL,
                          `ALLSKY_SFC_SW_DWN` DOUBLE NOT NULL,
                          PRIMARY KEY (`id`),
                          INDEX `fk_ALLSKY_SFC_SW_DWN_1_idx` (`point_id` ASC),
                          CONSTRAINT `fk_ALLSKY_SFC_SW_DWN_1`
                            FOREIGN KEY (`point_id`)
                            REFERENCES `nasa_solarview`.`point` (`id`)
                            ON DELETE NO ACTION
                            ON UPDATE NO ACTION);
                        """)

        cursor.execute("""
                        create spatial index ix_spatial_point_pt ON point(pt);
                        """)

    except:
        pass

    # Executa o comando:
    conexao.commit()

    # Finaliza a conexão
    conexao.close()
    

# Conectando ao banco de dados
def salvar_irradiacao(dados):
    conexao = pegar_conexao()
    """
    Cria localização e salva dados de irradiação
    ===
    
    conexao: conexao com banco de dados
    """
    try:
         with conexao.cursor() as cursor:
    # Criando ponto
            query = "INSERT INTO `nasa_solarview`.`point` (`pt`,`alt`) VALUES (GeomFromText('POINT({} {})'), {});".format(dados['longitude'],dados['latitude'],dados['altitude'])
            cursor.execute(query)
            conexao.commit()

    # Recuperando id do ponto recem criado
            query = "select id from `nasa_solarview`.`point` where st_contains(pt, point({}, {}));".format(dados['longitude'],dados['latitude'])
            cursor.execute(query)
            result = cursor.fetchone()
            point_id = result[0]

    # Agrupando valores
            values = []
            for key, value in dados['irradiacao'].items():
                time_in_datetime = datetime.strptime(key, "%Y%m%d")
                date = '{0:%Y}-{0:%m}-{0:%d}'.format(time_in_datetime)
                values.append(str((point_id, date, str(value))))

    # Criando query de inserção
            insert_query = "INSERT INTO `nasa_solarview`.`irradiacao` (`point_id`,`date`, `ALLSKY_SFC_SW_DWN`) VALUES {}".format(", ".join(values))
            cursor.execute(insert_query)
            conexao.commit()

    finally:
        conexao.close()

# Recuperar irracação da api da NASA
def get_irradiacao(lon = '', lat = ''):
    """
    Recupera irradiação solar para um ponto específico
    ===
    lat: latitide
    lon: longitude
    """
    
    # Definindo URL de requisição
    url = "https://power.larc.nasa.gov/cgi-bin/v1/DataAccess.py"
    
    # payload
    payload = {
        "request": "execute",
        "identifier": "SinglePoint",
        "parameters": "ALLSKY_SFC_SW_DWN",
        "startDate": "20180101",
        "endDate": "20181231",
        "userCommunity": "SSE",
        "tempAverage": "DAILY",
        "outputList": "JSON,ASCII",
        "lat": lat,
        "lon": lon,
        "user": "anonymous"
        }    

    response = requests.get(url,params = payload)
    json_data = response.json()

    coordinates = json_data['features'][0]['geometry']['coordinates']
    ALLSKY_SFC_SW_DWN = json_data['features'][0]['properties']['parameter']['ALLSKY_SFC_SW_DWN']
    
    return {'longitude': coordinates[0], 
            'latitude': coordinates[1], 
            'altitude': coordinates[2],
            'irradiacao': ALLSKY_SFC_SW_DWN
           }