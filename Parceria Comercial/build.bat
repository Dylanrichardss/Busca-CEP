@echo off
REM ============================================================
REM  Build do "Parceria Comercial OWN" (gera o .exe)
REM  Rode este arquivo na pasta onde estao:
REM    parceria_comercial.py, Arquivo - Parceiro.xlsx,
REM    logo.ico e logo.png
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo === [1/4] Criando ambiente virtual limpo (.venv) ===
python -m venv .venv
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale o Python 3 e marque "Add to PATH".
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat

echo.
echo === [2/4] Instalando apenas as dependencias necessarias ===
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo === [3/4] Gerando o executavel ===
REM  --onedir : gera uma PASTA com o .exe e as DLLs soltas (menos falso-positivo
REM             que o --onefile, que descompacta em pasta temporaria ao abrir)
REM  --noupx  : nao usa compressao UPX (muito associada a malware pelos antivirus)
pyinstaller ^
  --onedir ^
  --noupx ^
  --windowed ^
  --name "Parceria Comercial OWN" ^
  --icon "logo.ico" ^
  --add-data "logo.ico;." ^
  --add-data "logo.png;." ^
  --clean ^
  --noconfirm ^
  parceria_comercial.py

echo.
echo === [4/4] Copiando o Arquivo - Parceiro.xlsx para junto do .exe ===
if exist "Arquivo - Parceiro.xlsx" (
    copy /Y "Arquivo - Parceiro.xlsx" "dist\Parceria Comercial OWN\" >nul
    echo Copiado.
) else (
    echo ATENCAO: "Arquivo - Parceiro.xlsx" nao encontrado. Copie manualmente
    echo para "dist\Parceria Comercial OWN\" (a MESMA pasta do .exe).
)

echo.
echo Pronto!
echo O executavel e:  dist\Parceria Comercial OWN\Parceria Comercial OWN.exe
echo Para distribuir, compacte a pasta "Parceria Comercial OWN" inteira.
echo.
pause
