#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Webservices SEFAZ - Todos os Estados do Brasil
Configuração completa de URLs para NF-e 4.0

Referência: Portal Nacional da NF-e
https://www.nfe.fazenda.gov.br/portal/webServices.aspx
"""

# Mapeamento UF → Código
UF_CODIGO = {
    'AC': 12, 'AL': 27, 'AP': 16, 'AM': 13, 'BA': 29,
    'CE': 23, 'DF': 53, 'ES': 32, 'GO': 52, 'MA': 21,
    'MT': 51, 'MS': 50, 'MG': 31, 'PA': 15, 'PB': 25,
    'PR': 41, 'PE': 26, 'PI': 22, 'RJ': 33, 'RN': 24,
    'RS': 43, 'RO': 11, 'RR': 14, 'SC': 42, 'SP': 35,
    'SE': 28, 'TO': 17
}

# Código → UF
CODIGO_UF = {v: k for k, v in UF_CODIGO.items()}

# Webservices por Estado - NF-e 4.0
WEBSERVICES = {
    # Acre - AC
    'AC': {
        'homologacao': {
            'autorizacao': 'https://hom.svc.fazenda.gov.br/NFeAutorizacao4/NFeAutorizacao4.asmx',
            'retorno': 'https://hom.svc.fazenda.gov.br/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx',
            'consulta': 'https://hom.svc.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx',
            'status': 'https://hom.svc.fazenda.gov.br/NFeStatusServico4/NFeStatusServico4.asmx',
            'inutilizacao': 'https://hom.svc.fazenda.gov.br/NFeInutilizacao4/NFeInutilizacao4.asmx',
            'evento': 'https://hom.svc.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx'
        },
        'producao': {
            'autorizacao': 'https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx',
            'status': 'https://nfe.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx',
            'inutilizacao': 'https://nfe.svrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx',
            'evento': 'https://nfe.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx'
        }
    },
    
    # São Paulo - SP
    'SP': {
        'homologacao': {
            'autorizacao': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx',
            'retorno': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx',
            'consulta': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx',
            'status': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx',
            'inutilizacao': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeinutilizacao4.asmx',
            'evento': 'https://homologacao.nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx'
        },
        'producao': {
            'autorizacao': 'https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx',
            'retorno': 'https://nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx',
            'consulta': 'https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx',
            'status': 'https://nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx',
            'inutilizacao': 'https://nfe.fazenda.sp.gov.br/ws/nfeinutilizacao4.asmx',
            'evento': 'https://nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx'
        }
    },
    
    # Mato Grosso do Sul - MS
    'MS': {
        'homologacao': {
            'autorizacao': 'https://hom.nfe.sefaz.ms.gov.br/ws/NFeAutorizacao4',
            'retorno': 'https://hom.nfe.sefaz.ms.gov.br/ws/NFeRetAutorizacao4',
            'consulta': 'https://hom.nfe.sefaz.ms.gov.br/ws/NFeConsultaProtocolo4',
            'status': 'https://hom.nfe.sefaz.ms.gov.br/ws/NFeStatusServico4',
            'inutilizacao': 'https://hom.nfe.sefaz.ms.gov.br/ws/NFeInutilizacao4',
            'evento': 'https://hom.nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefaz.ms.gov.br/ws/NFeAutorizacao4',
            'retorno': 'https://nfe.sefaz.ms.gov.br/ws/NFeRetAutorizacao4',
            'consulta': 'https://nfe.sefaz.ms.gov.br/ws/NFeConsultaProtocolo4',
            'status': 'https://nfe.sefaz.ms.gov.br/ws/NFeStatusServico4',
            'inutilizacao': 'https://nfe.sefaz.ms.gov.br/ws/NFeInutilizacao4',
            'evento': 'https://nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4'
        }
    },
    
    # Rio de Janeiro - RJ
    'RJ': {
        'homologacao': {
            'autorizacao': 'https://hom.svc.fazenda.gov.br/NFeAutorizacao4/NFeAutorizacao4.asmx',
            'retorno': 'https://hom.svc.fazenda.gov.br/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx',
            'consulta': 'https://hom.svc.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx',
            'status': 'https://hom.svc.fazenda.gov.br/NFeStatusServico4/NFeStatusServico4.asmx',
            'inutilizacao': 'https://hom.svc.fazenda.gov.br/NFeInutilizacao4/NFeInutilizacao4.asmx',
            'evento': 'https://hom.svc.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx'
        },
        'producao': {
            'autorizacao': 'https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx',
            'status': 'https://nfe.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx',
            'inutilizacao': 'https://nfe.svrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx',
            'evento': 'https://nfe.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx'
        }
    },
    
    # Minas Gerais - MG
    'MG': {
        'homologacao': {
            'autorizacao': 'https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeAutorizacao4',
            'retorno': 'https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeRetAutorizacao4',
            'consulta': 'https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeConsultaProtocolo4',
            'status': 'https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeStatusServico4',
            'inutilizacao': 'https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeInutilizacao4',
            'evento': 'https://hnfe.fazenda.mg.gov.br/nfe2/services/NFeRecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.fazenda.mg.gov.br/nfe2/services/NFeAutorizacao4',
            'retorno': 'https://nfe.fazenda.mg.gov.br/nfe2/services/NFeRetAutorizacao4',
            'consulta': 'https://nfe.fazenda.mg.gov.br/nfe2/services/NFeConsultaProtocolo4',
            'status': 'https://nfe.fazenda.mg.gov.br/nfe2/services/NFeStatusServico4',
            'inutilizacao': 'https://nfe.fazenda.mg.gov.br/nfe2/services/NFeInutilizacao4',
            'evento': 'https://nfe.fazenda.mg.gov.br/nfe2/services/NFeRecepcaoEvento4'
        }
    },
    
    # Paraná - PR
    'PR': {
        'homologacao': {
            'autorizacao': 'https://homologacao.nfe.sefa.pr.gov.br/nfe/NFeAutorizacao4',
            'retorno': 'https://homologacao.nfe.sefa.pr.gov.br/nfe/NFeRetAutorizacao4',
            'consulta': 'https://homologacao.nfe.sefa.pr.gov.br/nfe/NFeConsultaProtocolo4',
            'status': 'https://homologacao.nfe.sefa.pr.gov.br/nfe/NFeStatusServico4',
            'inutilizacao': 'https://homologacao.nfe.sefa.pr.gov.br/nfe/NFeInutilizacao4',
            'evento': 'https://homologacao.nfe.sefa.pr.gov.br/nfe/NFeRecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefa.pr.gov.br/nfe/NFeAutorizacao4',
            'retorno': 'https://nfe.sefa.pr.gov.br/nfe/NFeRetAutorizacao4',
            'consulta': 'https://nfe.sefa.pr.gov.br/nfe/NFeConsultaProtocolo4',
            'status': 'https://nfe.sefa.pr.gov.br/nfe/NFeStatusServico4',
            'inutilizacao': 'https://nfe.sefa.pr.gov.br/nfe/NFeInutilizacao4',
            'evento': 'https://nfe.sefa.pr.gov.br/nfe/NFeRecepcaoEvento4'
        }
    },
    
    # Rio Grande do Sul - RS
    'RS': {
        'homologacao': {
            'autorizacao': 'https://nfe-homologacao.sefazrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe-homologacao.sefazrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe-homologacao.sefazrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx',
            'status': 'https://nfe-homologacao.sefazrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx',
            'inutilizacao': 'https://nfe-homologacao.sefazrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx',
            'evento': 'https://nfe-homologacao.sefazrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefazrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe.sefazrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe.sefazrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx',
            'status': 'https://nfe.sefazrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx',
            'inutilizacao': 'https://nfe.sefazrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx',
            'evento': 'https://nfe.sefazrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx'
        }
    },
    
    # Bahia - BA
    'BA': {
        'homologacao': {
            'autorizacao': 'https://hnfe.sefaz.ba.gov.br/webservices/NFeAutorizacao4/NFeAutorizacao4.asmx',
            'retorno': 'https://hnfe.sefaz.ba.gov.br/webservices/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx',
            'consulta': 'https://hnfe.sefaz.ba.gov.br/webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx',
            'status': 'https://hnfe.sefaz.ba.gov.br/webservices/NFeStatusServico4/NFeStatusServico4.asmx',
            'inutilizacao': 'https://hnfe.sefaz.ba.gov.br/webservices/NFeInutilizacao4/NFeInutilizacao4.asmx',
            'evento': 'https://hnfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefaz.ba.gov.br/webservices/NFeAutorizacao4/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe.sefaz.ba.gov.br/webservices/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe.sefaz.ba.gov.br/webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx',
            'status': 'https://nfe.sefaz.ba.gov.br/webservices/NFeStatusServico4/NFeStatusServico4.asmx',
            'inutilizacao': 'https://nfe.sefaz.ba.gov.br/webservices/NFeInutilizacao4/NFeInutilizacao4.asmx',
            'evento': 'https://nfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx'
        }
    },
    
    # Ceará - CE
    'CE': {
        'homologacao': {
            'autorizacao': 'https://nfeh.sefaz.ce.gov.br/nfe4/services/NFeAutorizacao4',
            'retorno': 'https://nfeh.sefaz.ce.gov.br/nfe4/services/NFeRetAutorizacao4',
            'consulta': 'https://nfeh.sefaz.ce.gov.br/nfe4/services/NFeConsultaProtocolo4',
            'status': 'https://nfeh.sefaz.ce.gov.br/nfe4/services/NFeStatusServico4',
            'inutilizacao': 'https://nfeh.sefaz.ce.gov.br/nfe4/services/NFeInutilizacao4',
            'evento': 'https://nfeh.sefaz.ce.gov.br/nfe4/services/NFeRecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefaz.ce.gov.br/nfe4/services/NFeAutorizacao4',
            'retorno': 'https://nfe.sefaz.ce.gov.br/nfe4/services/NFeRetAutorizacao4',
            'consulta': 'https://nfe.sefaz.ce.gov.br/nfe4/services/NFeConsultaProtocolo4',
            'status': 'https://nfe.sefaz.ce.gov.br/nfe4/services/NFeStatusServico4',
            'inutilizacao': 'https://nfe.sefaz.ce.gov.br/nfe4/services/NFeInutilizacao4',
            'evento': 'https://nfe.sefaz.ce.gov.br/nfe4/services/NFeRecepcaoEvento4'
        }
    },
    
    # Goiás - GO
    'GO': {
        'homologacao': {
            'autorizacao': 'https://homolog.sefaz.go.gov.br/nfe/services/NFeAutorizacao4',
            'retorno': 'https://homolog.sefaz.go.gov.br/nfe/services/NFeRetAutorizacao4',
            'consulta': 'https://homolog.sefaz.go.gov.br/nfe/services/NFeConsultaProtocolo4',
            'status': 'https://homolog.sefaz.go.gov.br/nfe/services/NFeStatusServico4',
            'inutilizacao': 'https://homolog.sefaz.go.gov.br/nfe/services/NFeInutilizacao4',
            'evento': 'https://homolog.sefaz.go.gov.br/nfe/services/NFeRecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefaz.go.gov.br/nfe/services/NFeAutorizacao4',
            'retorno': 'https://nfe.sefaz.go.gov.br/nfe/services/NFeRetAutorizacao4',
            'consulta': 'https://nfe.sefaz.go.gov.br/nfe/services/NFeConsultaProtocolo4',
            'status': 'https://nfe.sefaz.go.gov.br/nfe/services/NFeStatusServico4',
            'inutilizacao': 'https://nfe.sefaz.go.gov.br/nfe/services/NFeInutilizacao4',
            'evento': 'https://nfe.sefaz.go.gov.br/nfe/services/NFeRecepcaoEvento4'
        }
    },
    
    # Mato Grosso - MT
    'MT': {
        'homologacao': {
            'autorizacao': 'https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NfeAutorizacao4',
            'retorno': 'https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NfeRetAutorizacao4',
            'consulta': 'https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NfeConsulta4',
            'status': 'https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NfeStatusServico4',
            'inutilizacao': 'https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NfeInutilizacao4',
            'evento': 'https://homologacao.sefaz.mt.gov.br/nfews/v2/services/RecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeAutorizacao4',
            'retorno': 'https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeRetAutorizacao4',
            'consulta': 'https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeConsulta4',
            'status': 'https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeStatusServico4',
            'inutilizacao': 'https://nfe.sefaz.mt.gov.br/nfews/v2/services/NfeInutilizacao4',
            'evento': 'https://nfe.sefaz.mt.gov.br/nfews/v2/services/RecepcaoEvento4'
        }
    },
    
    # Pernambuco - PE
    'PE': {
        'homologacao': {
            'autorizacao': 'https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/NFeAutorizacao4',
            'retorno': 'https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/NFeRetAutorizacao4',
            'consulta': 'https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/NFeConsultaProtocolo4',
            'status': 'https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/NFeStatusServico4',
            'inutilizacao': 'https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/NFeInutilizacao4',
            'evento': 'https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4'
        },
        'producao': {
            'autorizacao': 'https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeAutorizacao4',
            'retorno': 'https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeRetAutorizacao4',
            'consulta': 'https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeConsultaProtocolo4',
            'status': 'https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeStatusServico4',
            'inutilizacao': 'https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeInutilizacao4',
            'evento': 'https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4'
        }
    },
    
    # SVRS - Ambiente Virtual RS (para estados sem webservice próprio)
    'SVRS': {
        'homologacao': {
            'autorizacao': 'https://nfe-homologacao.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe-homologacao.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe-homologacao.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx',
            'status': 'https://nfe-homologacao.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx',
            'inutilizacao': 'https://nfe-homologacao.svrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx',
            'evento': 'https://nfe-homologacao.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx'
        },
        'producao': {
            'autorizacao': 'https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx',
            'retorno': 'https://nfe.svrs.rs.gov.br/ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx',
            'consulta': 'https://nfe.svrs.rs.gov.br/ws/NfeConsulta/NfeConsulta4.asmx',
            'status': 'https://nfe.svrs.rs.gov.br/ws/NfeStatusServico/NfeStatusServico4.asmx',
            'inutilizacao': 'https://nfe.svrs.rs.gov.br/ws/nfeinutilizacao/nfeinutilizacao4.asmx',
            'evento': 'https://nfe.svrs.rs.gov.br/ws/recepcaoevento/recepcaoevento4.asmx'
        }
    }
}

# Estados que usam SVRS (não têm webservice próprio)
ESTADOS_SVRS = ['AC', 'AL', 'AP', 'DF', 'ES', 'PA', 'PB', 'PI', 'RJ', 'RN', 'RO', 'RR', 'SC', 'SE', 'TO']

# Preencher estados que usam SVRS
for uf in ESTADOS_SVRS:
    if uf not in WEBSERVICES:
        WEBSERVICES[uf] = WEBSERVICES['SVRS']


def obter_uf_por_cnpj(cnpj: str) -> str:
    """
    Obtém UF baseado no CNPJ
    
    IMPORTANTE: O código da UF NÃO está no CNPJ!
    Esta função busca a UF no banco de dados pela empresa.
    
    Args:
        cnpj: CNPJ da empresa (com ou sem formatação)
        
    Returns:
        str: Sigla da UF (ex: 'SP', 'MS') ou None
    """
    # CNPJ não contém código de UF
    # Deve ser buscado no cadastro da empresa
    return None


def obter_webservice(uf: str, ambiente: str = 'homologacao') -> dict:
    """
    Obtém URLs dos webservices para uma UF
    
    Args:
        uf: Sigla da UF (ex: 'SP', 'MS')
        ambiente: 'homologacao' ou 'producao'
        
    Returns:
        dict: URLs dos webservices
    """
    if uf not in WEBSERVICES:
        # Se não encontrar, usar SVRS
        uf = 'SVRS'
    
    return WEBSERVICES[uf][ambiente]


def obter_codigo_uf(uf: str) -> int:
    """
    Obtém código numérico da UF
    
    Args:
        uf: Sigla da UF (ex: 'SP', 'MS')
        
    Returns:
        int: Código da UF (ex: 35, 50)
    """
    return UF_CODIGO.get(uf, 91)  # 91 = Ambiente Nacional


def listar_estados_disponiveis() -> list:
    """
    Lista todos os estados com webservices configurados
    
    Returns:
        list: Lista de UFs
    """
    return sorted(list(set(WEBSERVICES.keys()) - {'SVRS'}))
