#!/usr/bin/env python3
"""
Devin Recovery Script - Finops-Teste Project

Este script mostra exatamente onde o Devin parou na implementação
e fornece instruções claras para retomar o trabalho.

Uso: python recovery.py
"""

import json
import os
from datetime import datetime
from pathlib import Path


def load_progress():
    """Carrega o progresso atual do projeto"""
    progress_file = Path(".devin-progress.json")
    if not progress_file.exists():
        print("❌ Arquivo de progresso não encontrado!")
        return None
    
    with open(progress_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_header():
    """Imprime cabeçalho do relatório"""
    print("🤖 " + "="*60)
    print("   DEVIN RECOVERY REPORT - FINOPS-TESTE PROJECT")
    print("="*64)
    print()


def print_current_status(progress):
    """Imprime status atual do projeto"""
    setup = progress['project_setup_progress']
    
    print("📊 STATUS ATUAL:")
    print(f"   Fase: {setup['current_phase']}")
    print(f"   Última atualização: {setup['timestamp']}")
    print()
    
    current = setup['current_step']
    print("🎯 PASSO ATUAL:")
    print(f"   {current['step']}: {current['description']}")
    print(f"   Status: {current['status']}")
    print(f"   Iniciado em: {current['started_at']}")
    print()


def print_completed_steps(progress):
    """Imprime passos já completados"""
    completed = progress['project_setup_progress']['completed_steps']
    
    print("✅ PASSOS COMPLETADOS:")
    for step in completed:
        print(f"   {step['step']}: {step['description']}")
        print(f"      ├── Status: {step['status']}")
        print(f"      ├── Timestamp: {step['timestamp']}")
        print(f"      └── Detalhes: {step['details']}")
        print()


def print_next_steps(progress):
    """Imprime próximos passos a serem executados"""
    next_steps = progress['project_setup_progress']['next_steps']
    
    print("📋 PRÓXIMOS PASSOS:")
    for i, step in enumerate(next_steps[:5], 1):  # Mostra próximos 5 passos
        print(f"   {step['step']}: {step['description']}")
        if 'files' in step:
            print("      Arquivos a criar:")
            for file in step['files']:
                print(f"         • {file}")
        print()


def print_files_status(progress):
    """Imprime status dos arquivos criados"""
    files_created = progress['project_setup_progress']['files_created']
    current_step = progress['project_setup_progress']['current_step']
    
    print("📁 ARQUIVOS CRIADOS:")
    for file in files_created:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file} (não encontrado)")
    print()
    
    if 'next_files_to_create' in current_step:
        print("📝 PRÓXIMOS ARQUIVOS A CRIAR:")
        for file in current_step['next_files_to_create']:
            print(f"   ⏳ {file}")
        print()


def print_architecture_decisions(progress):
    """Imprime decisões arquiteturais tomadas"""
    decisions = progress['project_setup_progress']['architecture_decisions']
    
    print("🏗️  DECISÕES ARQUITETURAIS:")
    for decision in decisions:
        print(f"   • {decision['decision']}")
        print(f"     Justificativa: {decision['rationale']}")
    print()


def print_recovery_instructions(progress):
    """Imprime instruções de recovery"""
    recovery = progress['recovery_instructions']
    
    print("🔄 COMO RETOMAR O TRABALHO:")
    for i, instruction in enumerate(recovery['how_to_resume'], 1):
        print(f"   {i}. {instruction}")
    print()
    
    print("⚡ PRINCÍPIOS CHAVE A MANTER:")
    for principle in recovery['key_principles_to_maintain']:
        print(f"   • {principle}")
    print()
    
    print("📚 ARQUIVOS DE REFERÊNCIA CRÍTICOS:")
    for file in recovery['critical_files_reference']:
        print(f"   • {file}")
    print()


def print_requirements_summary(progress):
    """Imprime resumo dos requisitos"""
    req = progress['project_setup_progress']['requirements_analysis']
    
    print("📋 RESUMO DOS REQUISITOS:")
    print("   Funcionais:")
    for req_item in req['functional_requirements'][:5]:  # Top 5
        print(f"      • {req_item}")
    
    print("   Não-funcionais:")
    for req_item in req['non_functional_requirements'][:5]:  # Top 5
        print(f"      • {req_item}")
    print()


def print_quick_commands():
    """Imprime comandos úteis para continuar"""
    print("🚀 COMANDOS ÚTEIS PARA CONTINUAR:")
    print("   # Ver estrutura atual do projeto")
    print("   tree backend/ frontend/ -I '__pycache__'")
    print()
    print("   # Verificar arquivos Python criados")
    print("   find . -name '*.py' -newer .devin-progress.json")
    print()
    print("   # Executar testes (quando disponível)")
    print("   cd backend && python -m pytest tests/ -v")
    print()
    print("   # Verificar qualidade do código")
    print("   cd backend && python -m flake8 internal/")
    print()


def main():
    """Função principal do script de recovery"""
    print_header()
    
    progress = load_progress()
    if not progress:
        return
    
    print_current_status(progress)
    print_completed_steps(progress)
    print_files_status(progress)
    print_next_steps(progress)
    print_architecture_decisions(progress)
    print_requirements_summary(progress)
    print_recovery_instructions(progress)
    print_quick_commands()
    
    print("🎯 RESUMO EXECUTIVO:")
    print("   O Devin estava implementando a arquitetura base do projeto Finops-Teste")
    print("   seguindo Clean Architecture + DDD. Já foram criadas as entidades de")
    print("   domínio e casos de uso. O próximo passo é criar os controllers.")
    print()
    print("💡 PARA CONTINUAR:")
    print("   Diga ao Devin: 'Continue de onde parou implementando os controllers'")
    print("   ou 'Execute o passo 1.5 do recovery'")
    print()


if __name__ == "__main__":
    main()