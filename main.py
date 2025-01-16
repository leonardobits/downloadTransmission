import os
import requests
import subprocess

def download_chunks(
    base_url: str,
    chunk_prefix: str = "video",
    chunk_suffix: str = ".ts",
    output_dir: str = "./chunks",
    headers: dict = None,
    start_chunk: int = 1
) -> int:
    """
    Baixa chunks sequenciais de um endpoint, assumindo que eles estejam
    nomeados de forma crescente, como video1.ts, video2.ts etc.

    Parâmetros:
    -----------
    base_url : str
        URL base, terminada com '/', onde os chunks podem ser acessados.
    chunk_prefix : str
        Prefixo do nome do chunk (ex: 'video').
    chunk_suffix : str
        Extensão ou sufixo do chunk (ex: '.ts').
    output_dir : str
        Diretório onde os arquivos .ts serão salvos.
    headers : dict
        Cabeçalhos HTTP opcionais para a requisição.
    start_chunk : int
        Número inicial do chunk para começar o download.

    Retorna:
    --------
    int
        Último chunk que foi baixado com sucesso. Retorna 0 se nenhum chunk for baixado.
    """

    os.makedirs(output_dir, exist_ok=True)
    chunk_number = start_chunk
    downloaded_any = False

    print("Iniciando download dos chunks...")

    while True:
        chunk_name = f"{chunk_prefix}{chunk_number}{chunk_suffix}"
        url = f"{base_url}{chunk_name}"
        output_file = os.path.join(output_dir, chunk_name)

        # Se o arquivo já existe, pula
        if os.path.exists(output_file):
            print(f"Chunk '{chunk_name}' já existe em '{output_dir}'. Pulando...")
            chunk_number += 1
            continue

        print(f"Baixando: {url}")
        response = requests.get(url, headers=headers or {})

        # Se não for 200 (OK), assume que não há mais chunks
        if response.status_code != 200:
            print(f"Parando. Resposta HTTP {response.status_code} para '{chunk_name}'.")
            break

        # Salva o chunk localmente
        with open(output_file, "wb") as f:
            f.write(response.content)

        downloaded_any = True
        chunk_number += 1

    # Se não baixou nenhum chunk, retorne 0
    if not downloaded_any:
        print("Nenhum chunk foi baixado.")
        return 0

    # O último chunk com sucesso foi o anterior ao que retornou != 200
    last_chunk = chunk_number - 1
    print(f"Último chunk baixado com sucesso: {last_chunk}")
    return last_chunk


def create_concat_file(output_dir: str, last_chunk: int,
                       chunk_prefix: str = "video", chunk_suffix: str = ".ts") -> str:
    """
    Cria um arquivo de concatenação para o ffmpeg (file_list.txt) contendo
    todos os chunks até last_chunk.

    Parâmetros:
    -----------
    output_dir : str
        Caminho para o diretório onde estão os chunks.
    last_chunk : int
        Índice do último chunk baixado.
    chunk_prefix : str
        Prefixo do nome do chunk (ex: 'video').
    chunk_suffix : str
        Extensão ou sufixo do chunk (ex: '.ts').

    Retorna:
    --------
    str
        Caminho completo para o arquivo de concatenação gerado.
    """

    concat_path = os.path.join(output_dir, "file_list.txt")
    print("Criando arquivo de concatenação:", concat_path)

    with open(concat_path, "w") as f:
        for i in range(1, last_chunk + 1):
            chunk_name = f"{chunk_prefix}{i}{chunk_suffix}"
            f.write(f"file '{chunk_name}'\n")

    return concat_path


def merge_chunks_into_mp4(concat_file_path: str, output_mp4: str):
    """
    Utiliza ffmpeg para unir todos os chunks .ts em um único arquivo .mp4.

    Parâmetros:
    -----------
    concat_file_path : str
        Caminho para o arquivo de concatenação.
    output_mp4 : str
        Nome ou caminho do arquivo final em .mp4.
    """

    print(f"Iniciando a conversão para {output_mp4}...")
    ffmpeg_command = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file_path,
        "-c", "copy",
        output_mp4
    ]
    subprocess.run(ffmpeg_command, check=True)
    print(f"Conversão finalizada! Arquivo gerado: {output_mp4}")


def main():
    # -----------------------------------------------------
    # Configurações gerais
    # -----------------------------------------------------
    base_url = "https://SEU_URL_DE_CHUNKS_AQUI/"  # Exemplo: https://exemplo.com/pasta/
    chunk_prefix = "video"                       # Exemplo: "video", "chunk", etc.
    chunk_suffix = ".ts"                         # Normalmente .ts, mas pode variar
    output_dir = "./chunks"                      # Diretório para os arquivos .ts
    output_mp4 = "minha_transmissao.mp4"         # Nome do arquivo final
    headers = {
        "User-Agent": "Mozilla/5.0"
        # Adicione ou remova cabeçalhos conforme necessário
    }

    # -----------------------------------------------------
    # Fluxo de execução
    # -----------------------------------------------------
    # 1) Baixar chunks
    last_chunk_downloaded = download_chunks(
        base_url=base_url,
        chunk_prefix=chunk_prefix,
        chunk_suffix=chunk_suffix,
        output_dir=output_dir,
        headers=headers
    )

    # 2) Se nenhum chunk foi baixado, encerrar
    if last_chunk_downloaded == 0:
        print("Encerrando script. Nenhum chunk válido foi encontrado.")
        return

    # 3) Criar arquivo de concatenação para o ffmpeg
    concat_file_path = create_concat_file(
        output_dir=output_dir,
        last_chunk=last_chunk_downloaded,
        chunk_prefix=chunk_prefix,
        chunk_suffix=chunk_suffix
    )

    # 4) Juntar e converter os chunks em .mp4 usando ffmpeg
    merge_chunks_into_mp4(concat_file_path, output_mp4)

    print("Processo concluído com sucesso!")


if __name__ == "__main__":
    main()
