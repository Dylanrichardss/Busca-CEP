# Busca-CEP
<b> App Python com interface gráfica de busca de informações a partir do CEP.</b>

## Demonstração

Página incial. Digitando o CEP e apertando Enter.

![image](https://github.com/user-attachments/assets/61357a93-4418-4d6c-ac8c-abccdc6ef9d3)

O app traz o Endereço, Bairro, Cidade e link para acessar o Google Maps.

![image](https://github.com/user-attachments/assets/5a5f72c7-25b0-43c8-86a0-eb6263c56a92)

![image](https://github.com/user-attachments/assets/1f6ddfac-71cc-4c2b-9ecc-43b11658eef2)



## Ferramentas usadas

- Python
- Requests
- Tkinter
- Webbrowser

``` bash
r = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
dados = r.json()
```
