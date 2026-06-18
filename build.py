import os
import subprocess
import shutil

# Função responsável por realizar o build da aplicação usando o PyInstaller
def build_app():
    print("Iniciando a criação do executável do TCC Lucass 13 Bus...")
    
    # Limpa as pastas antigas para evitar o erro de cache (Acesso negado) do PyInstaller
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"Limpando a pasta '{folder}'...")
            shutil.rmtree(folder, ignore_errors=True)

    # Linha de comando para o PyInstaller
    command = [
        "pyinstaller",
        "--noconfirm",
        "--name", "TCC Lucass 13 Bus",
        "--windowed",
        "--onefile",
        "--icon", "Logo.png",
        "--add-data", "Logo.png;.",
        "main.py"
    ]

    print(f"\nExecutando o comando: {' '.join(command)}\n")
    
    try:
        subprocess.run(command, check=True)
        print("\n" + "="*50)
        print("SUCESSO! O executável foi gerado corretamente.")
        print("Você pode encontrá-lo dentro da pasta 'dist/TCC Lucas 13 Bus'.")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print("\n" + "="*50)
        print(f"ERRO: A criação do executável falhou com o código {e.returncode}.")
        print("="*50)

if __name__ == "__main__":
    build_app()
