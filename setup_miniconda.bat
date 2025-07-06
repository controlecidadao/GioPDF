@echo off
setlocal enabledelayedexpansion
chcp 65001

REM Definir diretórios
set "SCRIPT_DIR=%~dp0"
set "MINICONDA_DIR=%SCRIPT_DIR%miniconda3"
set "DOWNLOAD_DIR=%SCRIPT_DIR%downloads"
set "INSTALLER_FILE=%DOWNLOAD_DIR%\Miniconda3-latest-Windows-x86_64.exe"

echo.
echo ============================================================================
echo    INSTALADOR AUTOMATIZADO - MINICONDA3 + AMBIENTE VIRTUAL GIOPDF
echo ============================================================================
echo.
echo Diretório do script: %SCRIPT_DIR%
echo Diretório do Miniconda: %MINICONDA_DIR%
echo.

REM Criar diretório de downloads se não existir
if not exist "%DOWNLOAD_DIR%" (
    echo Criando diretório de downloads...
    mkdir "%DOWNLOAD_DIR%"
)

REM Verificar se o Miniconda já está instalado
if exist "%MINICONDA_DIR%\Scripts\conda.exe" (
    echo Miniconda já está instalado em: %MINICONDA_DIR%
    goto :create_environment
)

REM Baixar o Miniconda3
echo Baixando Miniconda3...
echo Isso pode demorar alguns minutos dependendo da sua conexão...

powershell -Command "& {$ProgressPreference = 'Continue'; Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile '%INSTALLER_FILE%'}"

if not exist "%INSTALLER_FILE%" (
    echo ERRO: Falha ao baixar o Miniconda3!
    echo Verifique sua conexão com a internet e tente novamente.
    pause
    exit /b 1
)

echo Download concluído com sucesso!
echo.

REM Instalar o Miniconda3
echo Instalando Miniconda3...
echo Aguarde, a instalação está em progresso...

"%INSTALLER_FILE%" /InstallationType=JustMe /RegisterPython=0 /S /D=%MINICONDA_DIR%

:wait_installation
timeout /t 5 /nobreak >nul
if not exist "%MINICONDA_DIR%\Scripts\conda.exe" (
    echo Aguardando conclusão da instalação...
    goto :wait_installation
)

echo Miniconda3 instalado com sucesso!
echo.

REM Limpar arquivo de instalação
echo Limpando arquivos temporários...
if exist "%INSTALLER_FILE%" del "%INSTALLER_FILE%"

:create_environment
REM Configurar o ambiente
echo Configurando ambiente conda...
set "PATH=%MINICONDA_DIR%\Scripts;%MINICONDA_DIR%\condabin;%PATH%"

call "%MINICONDA_DIR%\Scripts\conda.exe" init cmd.exe >nul 2>&1

call "%MINICONDA_DIR%\Scripts\conda.exe" env list | findstr "giopdf" >nul
if %errorLevel% equ 0 (
    echo Ambiente 'giopdf' já existe. Removendo ambiente anterior...
    call "%MINICONDA_DIR%\Scripts\conda.exe" env remove -n giopdf -y
)

echo Criando ambiente virtual 'giopdf' com Python 3.10...
call "%MINICONDA_DIR%\Scripts\conda.exe" create -n giopdf python=3.10 -y

if %errorLevel% neq 0 (
    echo ERRO: Falha ao criar o ambiente virtual!
    pause
    exit /b 1
)

echo Ambiente virtual 'giopdf' criado com sucesso!
echo.

echo Ativando ambiente e atualizando pip...
call "%MINICONDA_DIR%\Scripts\activate.bat" giopdf
call "%MINICONDA_DIR%\envs\giopdf\Scripts\python.exe" -m pip install --upgrade pip

echo Pip atualizado com sucesso!
echo.

if exist "%SCRIPT_DIR%requirements.txt" (
    echo Instalando dependências do requirements.txt...
    call "%MINICONDA_DIR%\envs\giopdf\Scripts\pip.exe" install -r "%SCRIPT_DIR%requirements.txt"
    
    if %errorLevel% equ 0 (
        echo Dependências instaladas com sucesso!
    ) else (
        echo Algumas dependências podem ter falhado. Verifique os logs acima.
    )
    echo.
)

echo Criando script de ativação...
set "ACTIVATE_SCRIPT=%SCRIPT_DIR%activate_giopdf.bat"

echo @echo off > "%ACTIVATE_SCRIPT%"
echo REM Script para ativar o ambiente virtual giopdf >> "%ACTIVATE_SCRIPT%"
echo set "PATH=%MINICONDA_DIR%\Scripts;%MINICONDA_DIR%\condabin;%%PATH%%" >> "%ACTIVATE_SCRIPT%"
echo call "%MINICONDA_DIR%\Scripts\activate.bat" giopdf >> "%ACTIVATE_SCRIPT%"
echo echo. >> "%ACTIVATE_SCRIPT%"
echo echo Ambiente 'giopdf' ativado com sucesso! >> "%ACTIVATE_SCRIPT%"
echo echo Para executar a aplicação, use: streamlit run app.py >> "%ACTIVATE_SCRIPT%"
echo echo. >> "%ACTIVATE_SCRIPT%"
echo cmd /k >> "%ACTIVATE_SCRIPT%"

echo Script de ativação criado: %ACTIVATE_SCRIPT%
echo.

echo ============================================================================
echo                           INSTALAÇÃO CONCLUÍDA!
echo ============================================================================
echo.
echo Informações do ambiente:
echo   - Miniconda3 instalado em: %MINICONDA_DIR%
echo   - Ambiente virtual: giopdf
echo   - Versão Python: 3.10
echo.
echo Como usar:
echo   1. Execute: %ACTIVATE_SCRIPT%
echo   2. No terminal que abrir, use: streamlit run app.py
echo.
echo Comandos úteis:
echo   - Ativar ambiente: conda activate giopdf
echo   - Desativar ambiente: conda deactivate
echo   - Listar ambientes: conda env list
echo   - Instalar pacotes: pip install nome_do_pacote
echo.

echo Verificando instalação...
call "%MINICONDA_DIR%\Scripts\conda.exe" env list | findstr "giopdf"
if %errorLevel% equ 0 (
    echo ✓ Ambiente 'giopdf' confirmado!
) else (
    echo ✗ Erro na verificação do ambiente!
)

echo.
echo Pressione qualquer tecla para sair...
pause >nul

set /p "OPEN_ENV=Deseja abrir o ambiente agora? (s/n): "
if /i "%OPEN_ENV%"=="s" (
    start "" "%ACTIVATE_SCRIPT%"
)

echo Processo concluído!
exit /b 0