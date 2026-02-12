#!/usr/bin/env python3
"""Generate causas raiz semantico JSON for PicPay MLB 25Q4."""
import json
import os

data = {
    "metadata": {
        "player": "PicPay",
        "site": "MLB",
        "quarter": "25Q4",
        "metodo": "analisis_semantico"
    },
    "causas_por_motivo": {
        "Financiamiento": {
            "total_comentarios_analizados": 91,
            "delta_pp": -1.8,
            "causas_raiz": [
                {
                    "titulo": "Nao liberacao de cartao de credito para clientes antigos com alta movimentacao e salario depositado na conta",
                    "descripcion": "Grande parte dos usuarios reclama que, apesar de terem conta ha anos e receberem salario pelo PicPay, nunca receberam oferta de cartao de credito - diferente de concorrentes como Nubank que oferecem credito com menos tempo de relacionamento",
                    "frecuencia_pct": 50,
                    "frecuencia_abs": 24,
                    "ejemplos": [
                        "Pq tenho ele a mais de anos ,tudo que recebo passa por la e nunca foi me oferecido creditos nenhum e em outros bancos com menos tempo e menos dinheiro foi",
                        "Tenho conta a muito tempo, recebo meu salario e nunca recebi a opcao de cartao de credito",
                        "No Pic Pay nao ha oferta de credito no cartao como NO NU BANK..."
                    ]
                },
                {
                    "titulo": "Limite de credito irrisorio (R$100) sem possibilidade de aumento, forcando modelo de credito por recarga propria",
                    "descripcion": "Usuarios que possuem cartao de credito reclamam de limites extremamente baixos e da impossibilidade de aumento, sendo obrigados a usar o modelo de credito por recarga (depositar dinheiro para ter limite)",
                    "frecuencia_pct": 15,
                    "frecuencia_abs": 7,
                    "ejemplos": [
                        "E ridiculo que um banco ofereca um cartao de credito com um limite de 100 reais.",
                        "Eu gostaria de um limite maior, mas o pic pay so me deixou com a opcao de criar meu proprio credito.",
                        "Tenho um cartao de credito e nao consigo aumentar meu limite."
                    ]
                },
                {
                    "titulo": "Taxas de juros abusivas em simulacoes de emprestimo e cartao que afastam clientes para concorrentes",
                    "descripcion": "Multiplos usuarios relatam que as taxas de juros em emprestimos e cartao sao significativamente mais altas que em outros bancos, tornando os produtos financeiros do PicPay pouco competitivos",
                    "frecuencia_pct": 23,
                    "frecuencia_abs": 11,
                    "ejemplos": [
                        "Pq ja fiz simulacao de emprestimo e nao gostei da taxa de juros",
                        "as taxas sao um pouco mais alta que em outros lugares e a funcionalidade e um pouco complicada",
                        "Taxa de juros alta"
                    ]
                },
                {
                    "titulo": "Ausencia de opcoes de emprestimo pessoal e parcelamento de adiantamento salarial",
                    "descripcion": "Usuarios buscam linhas de credito como emprestimo pessoal e parcelamento de salario que o PicPay nao oferece ou oferece com condicoes muito ruins, levando-os a manter outros bancos como principal",
                    "frecuencia_pct": 12,
                    "frecuencia_abs": 6,
                    "ejemplos": [
                        "Falta condicoes de emprestimo",
                        "Tem que ter opcoes de e emprestimo",
                        "Nao oferece parcelamento no adiantamento de salario"
                    ]
                }
            ]
        },
        "Seguridad": {
            "total_comentarios_analizados": 12,
            "delta_pp": -1.8,
            "causas_raiz": [
                {
                    "titulo": "Relatos recorrentes de dinheiro desaparecendo da conta sem devolucao nem explicacao por parte do PicPay",
                    "descripcion": "Usuarios e seus conhecidos relatam casos de dinheiro que some da carteira digital sem explicacao, e o PicPay nao devolve os valores nem oferece esclarecimento, gerando medo generalizado",
                    "frecuencia_pct": 30,
                    "frecuencia_abs": 3,
                    "ejemplos": [
                        "Ja tive conhecidos que perderam dinheiro pela falta de seguranca no banco e na conta",
                        "parente viuu relatos de pessoas que perderam dinheiro, que sumiu da conta",
                        "Casos de problemas na conta, cujo dinheiro some da carteira e nao devolvem"
                    ]
                },
                {
                    "titulo": "Percepcao de inseguranca e falta de credibilidade institucional por ser banco exclusivamente digital sem estrutura fisica",
                    "descripcion": "Varios usuarios expressam desconfianca no PicPay como instituicao financeira, sentindo que podem perder dinheiro a qualquer momento por nao ter estrutura fisica ou reputacao consolidada comparavel ao Nubank",
                    "frecuencia_pct": 40,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "eu nao vejo o picpay com um banco, tenho a impressao que posso perder o meu dinheiro a qualquer momento",
                        "Um bom banco para rendimento, porem sem muita credibilidade e nao me passa tanta seguranga quanto nubank",
                        "Nao me sinto tao segura por ser um banco digital"
                    ]
                },
                {
                    "titulo": "Vulnerabilidade na autenticacao por SMS que facilita acesso em caso de roubo e contas invadidas sem suporte de recuperacao",
                    "descripcion": "Usuarios identificam falha grave no sistema de recuperacao de senha via SMS (permite acesso facil em caso de roubo de celular) e relatam invasoes de conta sem suporte efetivo",
                    "frecuencia_pct": 30,
                    "frecuencia_abs": 3,
                    "ejemplos": [
                        "Voce consegue recuperar a senha facilmente somente com um SMS, caso roubem seu celular teriam acesso a sua conta com facilidade",
                        "Ja vi alguns relatos de pessoas que tiveram a conta do PicPay invadida e a instituicao nao prestou um bom suporte",
                        "Porque da ultima vez que precisei estornar uma compra, o atendimento foi pessimo, moroso e nao foi efetivo"
                    ]
                }
            ]
        },
        "Complejidad": {
            "total_comentarios_analizados": 29,
            "delta_pp": -1.2,
            "causas_raiz": [
                {
                    "titulo": "App instavel que trava e fica fora do ar em momentos criticos como transferencias e pagamentos urgentes",
                    "descripcion": "Usuarios relatam que o aplicativo apresenta instabilidade frequente, ficando fora do ar ou travando justamente quando precisam realizar operacoes financeiras urgentes",
                    "frecuencia_pct": 33,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "Quanto mais precisei o app nao funcionava ou o cartao dava fora do sistema",
                        "Fica fora do ar muitas vezes",
                        "Eu sinto um pouco insegura porque ja abri o app do banco e deu uma travada no dinheiro que estava precisando urgente"
                    ]
                },
                {
                    "titulo": "Interface confusa e design pouco intuitivo que dificulta localizar informacoes e entender o sistema de cartoes",
                    "descripcion": "Usuarios consideram o app confuso para navegar, com dados e informacoes dificeis de encontrar, e um design que nao convida ao uso - especialmente na gestao de cartoes",
                    "frecuencia_pct": 42,
                    "frecuencia_abs": 5,
                    "ejemplos": [
                        "Dificil de entender o sistema",
                        "Alguns dados ou informacoes, nao se acha no app",
                        "Acho confuso as vezes, e a questao de como obter e utilizar cartoes."
                    ]
                },
                {
                    "titulo": "Erros recorrentes em funcionalidades essenciais como Pix copia-e-cola e pagamento por QR Code nos caixas",
                    "descripcion": "Funcoes basicas do dia a dia apresentam falhas frequentes, como erros no Pix copia-e-cola e problemas no QR Code nos caixas, sem resolucao pelo SAC",
                    "frecuencia_pct": 25,
                    "frecuencia_abs": 3,
                    "ejemplos": [
                        "Sempre que vou fazer pix copia e cola apresenta erro",
                        "Problema no QR code nos caixas e SAC nao ajudou",
                        "As vezes a rede cai e nao tem como fazer transferencia"
                    ]
                }
            ]
        },
        "Atencion": {
            "total_comentarios_analizados": 29,
            "delta_pp": 1.0,
            "causas_raiz": [
                {
                    "titulo": "Impossibilidade de falar com atendente humano, sendo forcado a interagir com robo e chat automatizado ineficaz",
                    "descripcion": "A queixa mais frequente e a dificuldade extrema de conseguir falar com uma pessoa real - o atendimento e dominado por gravacoes e robos que nao compreendem os problemas dos clientes",
                    "frecuencia_pct": 38,
                    "frecuencia_abs": 9,
                    "ejemplos": [
                        "quando tive duvidas, nao encontrei uma forma de atendimento pessoal, apenas eletronico",
                        "Nao tem um bom atendimento. Falamos com uma gravacao, e os atendentes nao sao solicitos",
                        "Porque precisei contestar uma compra no meu cartao de credito e tive dificuldade com o atendimento do robo ate conseguir chegar em um atendente humano"
                    ]
                },
                {
                    "titulo": "Tempo de resposta excessivo com protocolos abertos que demoram uma eternidade sem retorno efetivo",
                    "descripcion": "Mesmo quando o contato e estabelecido, os prazos de retorno sao extremamente longos, com protocolos que ficam abertos sem resolucao por periodos indefinidos",
                    "frecuencia_pct": 29,
                    "frecuencia_abs": 7,
                    "ejemplos": [
                        "Atendimento ao cliente e pessimo. Em protocolos abertos, demoram uma eternidade para retorno. Produtos tambem sao falhos",
                        "A resposta do atendimento e demorado e muitas vezes seus atendentes nao compreendem o texto e acabam causando maior esforco pra resolver o processo.",
                        "Muita demora ao atender"
                    ]
                },
                {
                    "titulo": "Falta de resolucao efetiva de problemas criticos como fraudes no Pix e contestacoes de compra mesmo apos multiplos contatos",
                    "descripcion": "Usuarios relatam que, mesmo conseguindo atendimento, os problemas nao sao resolvidos - especialmente em casos graves como fraude no Pix e cobrancas indevidas de seguros nao contratados",
                    "frecuencia_pct": 33,
                    "frecuencia_abs": 8,
                    "ejemplos": [
                        "Tive problema com fraude/pix, cai num golpe e simplesmente nao obtive ajuda",
                        "Me aconteceu um caso com a picpay que fui vitima de fraude, e o atendimento e solucao do problema fui muito dificil.",
                        "Foram debitados 2 seguros que nao solicitei e nao consegui contato para cancelar e saber o que aconteceu"
                    ]
                }
            ]
        },
        "Promociones": {
            "total_comentarios_analizados": 27,
            "delta_pp": -1.0,
            "causas_raiz": [
                {
                    "titulo": "Eliminacao progressiva do cashback que era o principal diferencial e razao de adesao ao PicPay",
                    "descripcion": "Usuarios antigos relatam que o PicPay oferecia cashback em todas as compras e cupons de resgate, mas esses beneficios foram gradualmente removidos sem substituicao",
                    "frecuencia_pct": 40,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "Porque no comeco quando utilizava l Pix lay era um banco que oferecia bastante promocoes como cupom de cashback para resgate depois aos poucos foi acabando",
                        "Inicialmente Picpay tinha uma promocao de cashback em todas as compras, agora nao tem mais.",
                        "Antigamente a PicPay era mais interessante com promocoes e programas que beneficiavam o usuario, hoje nao beneficia mais, nao vejo vantagem em quase nada que oferecem"
                    ]
                },
                {
                    "titulo": "Ausencia de programas de fidelidade estruturados como pontos e milhas que bancos concorrentes ja oferecem",
                    "descripcion": "Usuarios comparam o PicPay com outros bancos e sentem falta de programas estruturados de pontos, milhas no cartao de credito e beneficios que incentivem o uso continuo",
                    "frecuencia_pct": 40,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "Nao tem muitos beneficios como clube de pontos etc",
                        "O banco nao tem cartao de credito com milhas",
                        "As possibilidade de promocoes e descontos nao sao atraentes."
                    ]
                },
                {
                    "titulo": "Burocracia para resgatar beneficios de indicacao e ausencia total de promocoes para clientes atuais",
                    "descripcion": "Os poucos beneficios que existem sao burocraticos para resgatar, e clientes novos e atuais nao recebem promocoes de boas-vindas ou incentivos para uso ativo da conta",
                    "frecuencia_pct": 20,
                    "frecuencia_abs": 2,
                    "ejemplos": [
                        "Burocratico para receber beneficio de indicacao",
                        "E um banco que estou comecando a usar, gostaria de ter algumas promocoes ou descontos usando a conta do picpay"
                    ]
                }
            ]
        },
        "Rendimientos": {
            "total_comentarios_analizados": 39,
            "delta_pp": -0.3,
            "causas_raiz": [
                {
                    "titulo": "Rendimento do saldo em conta muito abaixo de concorrentes como 99, Nubank e outros bancos digitais",
                    "descripcion": "A maioria dos detratores nesta categoria reclama que o rendimento do PicPay e significativamente inferior ao oferecido por outros bancos digitais, tornando-o pouco atrativo para guardar dinheiro",
                    "frecuencia_pct": 62,
                    "frecuencia_abs": 10,
                    "ejemplos": [
                        "Gosto das oportunidades, mas a 99 esta com maior rendimento do cdi.",
                        "tem contas melhores, nao vale a pena, sou o rendimento da conta corrente",
                        "Tem banco pagando mais em relacao com rendimento"
                    ]
                },
                {
                    "titulo": "Reducao do rendimento que era o principal atrativo de adesao, incluindo mudanca de rentabilidade diaria para mensal",
                    "descripcion": "Usuarios que entraram no PicPay pelo alto rendimento relatam que este foi progressivamente reduzido, com mudanca de capitalizacao diaria para mensal, quebrando a promessa inicial",
                    "frecuencia_pct": 25,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "bom banco, mais ofericia rentabilidade diaria e agora passou a mensal",
                        "O rendimento diminuiu",
                        "Porque o mais atrativo quando me tornei cliente deles foi o alto rendimento do dinheiro colocado la."
                    ]
                },
                {
                    "titulo": "Falta de produtos de investimento acessiveis tipo caixinha e interface confusa na area financeira do app",
                    "descripcion": "Usuarios sentem falta de opcoes como caixinha (reservas separadas por objetivo) que concorrentes oferecem, e acham a area de investimentos do aplicativo confusa e pouco didatica",
                    "frecuencia_pct": 13,
                    "frecuencia_abs": 2,
                    "ejemplos": [
                        "Falta um melhor rendimento, tipo caixinha!",
                        "Sou uma pessoa que ainda busca informacao sobre investimentos, acho o aplicativo confuso nesta questao, entao acabo que nao dando atencao a oque tem la por esta confuso"
                    ]
                }
            ]
        },
        "Tarifas": {
            "total_comentarios_analizados": 11,
            "delta_pp": 0.3,
            "causas_raiz": [
                {
                    "titulo": "Cobranca de tarifas por servicos basicos como emissao de boletos que bancos digitais concorrentes oferecem gratis",
                    "descripcion": "Usuarios percebem que o PicPay cobra por servicos que deveriam ser gratuitos em um banco digital, como emissao de boletos e outras operacoes basicas",
                    "frecuencia_pct": 43,
                    "frecuencia_abs": 3,
                    "ejemplos": [
                        "O pic pay tudo o que voce faz tem que pagar nao e um AP muito bom",
                        "Cobra as emissoes de boletos",
                        "Eles fazem cobranca"
                    ]
                },
                {
                    "titulo": "Taxas de juros e tarifas gerais significativamente mais altas que a concorrencia sem beneficios que justifiquem o custo",
                    "descripcion": "As tarifas e taxas de juros do PicPay sao percebidas como desproporcionalmente altas em comparacao com outros bancos, sem que haja beneficios ou diferenciais que justifiquem o custo adicional",
                    "frecuencia_pct": 57,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "Taxas muito altas",
                        "Podia ser.mais flexivel taxas de juros muito alta",
                        "A tarifa e um pouco  alta,poderia melhorar a oferta"
                    ]
                }
            ]
        },
        "Funcionalidades": {
            "total_comentarios_analizados": 22,
            "delta_pp": 0.1,
            "causas_raiz": [
                {
                    "titulo": "Ausencia de funcionalidades essenciais como investimento em renda variavel e ferramentas de gestao financeira pessoal",
                    "descripcion": "Usuarios sentem que o PicPay carece de funcionalidades importantes para ser um banco completo, como investimentos em renda variavel, aplicacoes diversificadas e ferramentas de controle financeiro",
                    "frecuencia_pct": 56,
                    "frecuencia_abs": 5,
                    "ejemplos": [
                        "Falta de investimento em renda variavel",
                        "Faltam muitas funcionalidades, rendimento, aplicacoes.",
                        "Nao apresenta nenhuma funcionalidade para os clientes. Deveria ser uma conta poupanca, nao banco com cartao de credito."
                    ]
                },
                {
                    "titulo": "Aplicativo complexo e pouco intuitivo que dificulta encontrar e utilizar as funcionalidades existentes",
                    "descripcion": "Mesmo as funcionalidades que existem sao dificeis de acessar devido a um aplicativo que nao e simples de navegar, com informacoes mal organizadas",
                    "frecuencia_pct": 44,
                    "frecuencia_abs": 4,
                    "ejemplos": [
                        "Aplicativo nao  e simples de mecher",
                        "App um pouco complicado de mexer",
                        "As vezes complica achar  as coisad"
                    ]
                }
            ]
        }
    }
}

output_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "causas_raiz_semantico_PicPay_MLB_25Q4.json"
)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"JSON written to: {output_path}")
for k, v in data["causas_por_motivo"].items():
    n_causas = len(v["causas_raiz"])
    total = v["total_comentarios_analizados"]
    delta = v["delta_pp"]
    pct_sum = sum(c["frecuencia_pct"] for c in v["causas_raiz"])
    print(f"  {k}: {n_causas} causas, {total} comments, delta={delta}pp, freq_sum={pct_sum}%")
