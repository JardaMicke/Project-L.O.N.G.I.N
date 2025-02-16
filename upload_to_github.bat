@echo off
setlocal enabledelayedexpansion

:: Nastavení proměnných
set /p GITHUB_URL=Zadejte celou URL adresu existujícího GitHub repozitáře (např. https://github.com/uzivatel/repozitar.git): 

:: Extrakce uživatelského jména z URL
for /f "tokens=4 delims=/" %%a in ("%GITHUB_URL%") do set GITHUB_USERNAME=%%a

echo Detekované uživatelské jméno: %GITHUB_USERNAME%

set /p GITHUB_PASSWORD=Zadejte vaše GitHub heslo (nebo osobní přístupový token): 

:: Inicializace lokálního Git repozitáře
echo Inicializuji lokální Git repozitář...
git init

:: Propojení s vzdáleným repozitářem
echo Propojuji s vzdáleným repozitářem...
git remote add origin https://%GITHUB_USERNAME%:%GITHUB_PASSWORD%@%GITHUB_URL:https://=%

:: Přidání všech souborů do staging area
echo Přidávám soubory do staging area...
git add .

:: Vytvoření prvního commitu
echo Vytvářím první commit...
git commit -m "Inicializace lokálního repozitáře a nahrání struktury adresářů"

:: Stažení existující historie z GitHub
echo Stahuji existující historii z GitHub...
git pull origin main --allow-unrelated-histories

:: Pokus o push
echo Nahrávám změny na GitHub...
git push -u origin main

echo Hotovo! Vaše adresářová struktura by měla být nyní na GitHubu.
pause
