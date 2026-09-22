# Escuta Planetária

Arquivo de relatos públicos de sonho e desejo.

Este repositório canônico (`JoaoCarabetta/escuta-planetaria`) foi semeado a partir do trabalho original de **[Fitipe](https://github.com/fitipe)** em [`fitipe/escuta-planetaria`](https://github.com/fitipe/escuta-planetaria).

## Branches

| Branch | Uso |
|--------|-----|
| `prod` | produção (branch padrão) |
| `joao` | staging de João |
| `filipe` | staging de Filipe |
| `main` | espelho da base upstream |

## Origem

Projeto iniciado por Fitipe (PPGCA/UFF). Ver também o site em `index.html` para contexto e créditos.

## Deploy (carabetta.xyz VPS)

Live URLs (path staging on one subdomain):

- Production (`prod`): https://escutaplanetaria.carabetta.xyz/
- João staging (`joao`): https://escutaplanetaria.carabetta.xyz/joao/
- Filipe staging (`filipe`): https://escutaplanetaria.carabetta.xyz/filipe/

Pushing to `prod`, `joao`, or `filipe` triggers `.github/workflows/deploy.yml`, which rsyncs static files to `/var/www/escutaplanetaria/<branch>/` on the Hetzner VPS. Nginx sample: `nginx/escutaplanetaria.carabetta.xyz.conf`.
