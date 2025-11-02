import os, uuid, pathlib, time, gc
from packages.adapters.embedder_adapter.sbert_embedder import SBertEmbedder
from packages.adapters.vector_repo_adapter.qdrant_repo import QdrantRepo
from packages.core.ports.vector_repo import VectorDoc

def chunk(text: str, size: int=800, overlap: int=150):
    """Cria chunks menores para economizar memória"""
    i=0; n=len(text)
    while i<n:
        j=min(n, i+size)
        yield text[i:j]
        i = j - overlap if j - overlap > 0 else j

def load_md(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")

if __name__ == "__main__":
    print("🚀 Iniciando indexação dos documentos...")
    
    embedder = SBertEmbedder()
    vector = QdrantRepo(embedder)
    
    # Primeiro, vamos contar quantos arquivos temos
    md_files = list(pathlib.Path("./normativos").glob("*.md"))
    total_files = len(md_files)
    
    if total_files == 0:
        print("❌ Nenhum arquivo .md encontrado na pasta ./normativos/")
        exit(1)
    
    print(f"📁 Encontrados {total_files} arquivos .md")
    
    start_time = time.time()
    total_chunks_processed = 0
    batch_size = 100  # Lotes bem pequenos para economizar memória
    
    # Processamento arquivo por arquivo (mais eficiente com memória)
    for file_idx, md in enumerate(md_files, 1):
        print(f"\n📖 [{file_idx}/{total_files}] Processando: {md.name}")
        
        try:
            # Carrega o arquivo
            text = load_md(str(md))
            file_chunks = 0
            docs_batch = []
            
            print(f"   📄 Arquivo carregado ({len(text):,} caracteres)")
            
            # Processa chunks em lotes pequenos
            for chunk_text in chunk(text):
                docs_batch.append({
                    "id": str(uuid.uuid4()), 
                    "text": chunk_text, 
                    "metadata": {"doc": md.name}
                })
                file_chunks += 1
                
                # Insere quando o lote fica cheio
                if len(docs_batch) >= batch_size:
                    print(f"   🔄 Inserindo lote de {len(docs_batch)} chunks...", end="", flush=True)
                    vector.upsert(docs_batch)
                    total_chunks_processed += len(docs_batch)
                    print(" ✅")
                    
                    # Limpa o lote da memória
                    docs_batch.clear()
                    gc.collect()
            
            # Insere os chunks restantes do arquivo
            if docs_batch:
                print(f"   🔄 Inserindo lote final de {len(docs_batch)} chunks...", end="", flush=True)
                vector.upsert(docs_batch)
                total_chunks_processed += len(docs_batch)
                print(" ✅")
                docs_batch.clear()
            
            print(f"   ✅ Arquivo concluído: {file_chunks} chunks criados")
            
            # Limpa variáveis grandes da memória
            del text
            gc.collect()
            
        except MemoryError:
            print(f"   ❌ Erro de memória ao processar {md.name}")
            print("   💡 Tente reduzir o batch_size ou reiniciar o processo")
            break
        except Exception as e:
            print(f"   ❌ Erro ao processar {md.name}: {e}")
            continue
        
        # Mostra progresso geral
        elapsed = time.time() - start_time
        if elapsed > 0:
            chunks_per_sec = total_chunks_processed / elapsed
            print(f"   📊 Total processado: {total_chunks_processed} chunks ({chunks_per_sec:.1f}/s)")
    
    total_time = time.time() - start_time
    
    print(f"\n🎉 Indexação concluída!")
    print(f"📈 Estatísticas finais:")
    print(f"   • Arquivos processados: {total_files}")
    print(f"   • Total de chunks indexados: {total_chunks_processed}")
    print(f"   • Tempo total: {total_time:.2f}s")
    if total_time > 0:
        print(f"   • Velocidade média: {total_chunks_processed/total_time:.1f} chunks/s")
    
    # Força limpeza final
    gc.collect()
    print("🧹 Limpeza de memória concluída")