import { useState } from 'react'

function App() {
  const [tema, setTema] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [briefing, setBriefing] = useState('')
  const [metricas, setMetricas] = useState(null)
  const [erro, setErro] = useState('')
  const [pendente, setPendente] = useState(null)

  const podeGerar = tema.trim().length > 0 && !carregando && !pendente
  const aguardandoAprovacao = pendente !== null

  function resetarEstado() {
    setBriefing('')
    setMetricas(null)
    setErro('')
    setPendente(null)
  }

  async function gerarBriefing(event) {
    event.preventDefault()
    if (!podeGerar) return

    setCarregando(true)
    resetarEstado()

    try {
      const resposta = await fetch('http://localhost:8000/api/briefing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tema: tema.trim() }),
      })

      if (!resposta.ok) {
        throw new Error(`Erro ${resposta.status} ao gerar briefing.`)
      }

      const dados = await resposta.json()
      if (dados.status === 'aguardando_aprovacao') {
        setPendente({
          thread_id: dados.thread_id,
          noticias: dados.noticias ?? '',
          memoria: dados.memoria ?? null,
        })
      } else {
        setBriefing(dados.briefing ?? '')
        setMetricas({
          tempo_ms: dados.tempo_ms,
          num_chamadas: dados.num_chamadas,
          memoria: dados.memoria,
        })
      }
    } catch (err) {
      setErro(err.message || 'Não foi possível gerar o briefing.')
    } finally {
      setCarregando(false)
    }
  }

  async function aprovarEContinuar() {
    if (!pendente || carregando) return
    setCarregando(true)
    setErro('')

    try {
      const resposta = await fetch(
        'http://localhost:8000/api/briefing/retomar',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ thread_id: pendente.thread_id }),
        },
      )

      if (!resposta.ok) {
        throw new Error(`Erro ${resposta.status} ao retomar briefing.`)
      }

      const dados = await resposta.json()
      setBriefing(dados.briefing ?? '')
      setMetricas({
        tempo_ms: dados.tempo_ms,
        num_chamadas: dados.num_chamadas,
        memoria: dados.memoria,
      })
      setPendente(null)
    } catch (err) {
      setErro(err.message || 'Não foi possível retomar o briefing.')
    } finally {
      setCarregando(false)
    }
  }

  function descartar() {
    resetarEstado()
  }

  return (
    <div className="relative min-h-full overflow-hidden bg-stone-50">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-gradient-to-b from-amber-100/60 via-amber-50/30 to-transparent"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-32 top-40 h-72 w-72 rounded-full bg-orange-200/40 blur-3xl"
      />

      <div className="relative mx-auto flex min-h-screen max-w-3xl flex-col px-6 py-12 sm:py-16">
        <header className="mb-12">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">
            <span className="inline-block h-2 w-2 rounded-full bg-amber-600" />
            NewsLens
          </div>
          <h1 className="font-serif mt-4 text-4xl font-semibold leading-[1.05] tracking-tight text-stone-900 sm:text-5xl">
            Briefing de notícias{' '}
            <span className="italic text-amber-700">sob demanda</span>.
          </h1>
          <p className="mt-4 max-w-xl text-[17px] leading-relaxed text-stone-600">
            Digite um tema e receba um resumo organizado, com contexto e o que
            observar a seguir.
          </p>
          <div className="mt-6 h-px w-16 bg-stone-300" />
        </header>

        <form onSubmit={gerarBriefing} className="space-y-3">
          <label
            htmlFor="tema"
            className="block text-xs font-semibold uppercase tracking-wider text-stone-500"
          >
            Tema
          </label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="tema"
              type="text"
              value={tema}
              onChange={(e) => setTema(e.target.value)}
              placeholder="Ex.: política monetária, eleições, IA generativa..."
              disabled={carregando}
              className="w-full rounded-lg border border-stone-300 bg-white px-4 py-3 text-stone-900 placeholder-stone-400 shadow-sm outline-none transition focus:border-amber-700 focus:ring-2 focus:ring-amber-700/20 disabled:cursor-not-allowed disabled:bg-stone-100"
            />
            <button
              type="submit"
              disabled={!podeGerar}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-stone-900 px-6 py-3 text-sm font-semibold text-stone-50 shadow-sm transition hover:bg-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-700/40 disabled:cursor-not-allowed disabled:bg-stone-300 disabled:text-stone-500"
            >
              {carregando ? (
                <>
                  <Spinner />
                  Gerando…
                </>
              ) : (
                <>
                  Gerar briefing
                  <ArrowIcon />
                </>
              )}
            </button>
          </div>
        </form>

        <section className="mt-12 flex-1">
          <div className="mb-3 flex items-center gap-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
              Resultado
            </h2>
            <div className="h-px flex-1 bg-stone-200" />
            {briefing && !carregando && (
              <span className="text-xs font-medium text-amber-700">
                pronto
              </span>
            )}
            {aguardandoAprovacao && !carregando && (
              <span className="text-xs font-medium text-amber-700">
                aguardando aprovação
              </span>
            )}
          </div>

          <div className="relative min-h-[18rem] overflow-hidden rounded-xl border border-stone-200 bg-white shadow-[0_1px_2px_rgba(28,25,23,0.04),0_8px_24px_-12px_rgba(28,25,23,0.12)]">
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-amber-600 via-orange-500 to-amber-600 opacity-80" />

            <div className="p-7">
              {carregando && <SkeletonBriefing />}

              {!carregando && erro && (
                <p className="text-sm text-red-700">{erro}</p>
              )}

              {!carregando && !erro && aguardandoAprovacao && (
                <PreviewAprovacao
                  noticias={pendente.noticias}
                  memoria={pendente.memoria}
                  onAprovar={aprovarEContinuar}
                  onDescartar={descartar}
                />
              )}

              {!carregando && !erro && !aguardandoAprovacao && !briefing && (
                <EmptyState />
              )}

              {!carregando && !erro && !aguardandoAprovacao && briefing && (
                <>
                  <article className="font-serif whitespace-pre-wrap text-[17px] leading-[1.7] text-stone-800">
                    {briefing}
                  </article>
                  {metricas && (
                    <div className="mt-6 border-t border-stone-100 pt-3 text-[11px] uppercase tracking-wider text-stone-400">
                      <div>
                        <span>{metricas.num_chamadas} chamada{metricas.num_chamadas === 1 ? '' : 's'}</span>
                        <span className="mx-2 text-stone-300">·</span>
                        <span>{metricas.tempo_ms} ms</span>
                      </div>
                      {metricas.memoria && (
                        <div className="mt-1.5 flex flex-wrap items-center gap-x-2">
                          <span className="font-medium text-stone-500">memória</span>
                          <span
                            aria-label={metricas.memoria.disponivel ? 'memória disponível' : 'memória indisponível'}
                            title={metricas.memoria.disponivel ? 'memória disponível' : 'memória indisponível'}
                            className={
                              'inline-block h-2 w-2 rounded-full ' +
                              (metricas.memoria.disponivel ? 'bg-emerald-500' : 'bg-red-500')
                            }
                          />
                          <span className="text-stone-300">·</span>
                          <span>1ª vez {metricas.memoria.primeira_vez ? 'sim' : 'não'}</span>
                          <span className="text-stone-300">·</span>
                          <span>
                            {metricas.memoria.briefings_anteriores_consultados} anterior{metricas.memoria.briefings_anteriores_consultados === 1 ? '' : 'es'}
                          </span>
                          <span className="text-stone-300">·</span>
                          <span>desde {formatarData(metricas.memoria.data_briefing_mais_antigo)}</span>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </section>

        <footer className="mt-12 flex items-center justify-between border-t border-stone-200 pt-6 text-xs text-stone-500">
          <span>NewsLens · protótipo</span>
          <span className="italic">resultado simulado</span>
        </footer>
      </div>
    </div>
  )
}

function formatarData(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso + 'T00:00:00')
    if (Number.isNaN(d.getTime())) return iso
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

function ArrowIcon() {
  return (
    <svg
      className="h-3.5 w-3.5"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M3 8h10m0 0L9 4m4 4l-4 4"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin text-stone-50"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  )
}

function PreviewAprovacao({ noticias, memoria, onAprovar, onDescartar }) {
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-x-2 text-[11px] uppercase tracking-wider text-stone-400">
        <span className="font-medium text-amber-700">Notícias coletadas</span>
        <span className="text-stone-300">·</span>
        <span>revise antes de gerar o briefing</span>
        {memoria && (
          <>
            <span className="text-stone-300">·</span>
            <span>
              {memoria.briefings_anteriores_consultados} briefing
              {memoria.briefings_anteriores_consultados === 1 ? '' : 's'} anterior
              {memoria.briefings_anteriores_consultados === 1 ? '' : 'es'}
            </span>
          </>
        )}
      </div>

      <article className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-md border border-stone-100 bg-stone-50/50 p-4 font-serif text-[15px] leading-[1.6] text-stone-700">
        {noticias || '(nenhuma notícia coletada)'}
      </article>

      <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-end">
        <button
          type="button"
          onClick={onDescartar}
          className="inline-flex items-center justify-center rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-medium text-stone-600 transition hover:bg-stone-50"
        >
          Descartar
        </button>
        <button
          type="button"
          onClick={onAprovar}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-amber-700 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-amber-800"
        >
          Aprovar e gerar briefing
          <ArrowIcon />
        </button>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-[14rem] flex-col items-center justify-center text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-amber-700">
        <svg
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M4 6h16M4 12h10M4 18h16"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <p className="mt-4 text-stone-500">
        O briefing aparecerá aqui assim que você gerar um tema.
      </p>
    </div>
  )
}

function SkeletonBriefing() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-3 w-1/3 rounded bg-stone-200" />
      <div className="h-3 w-full rounded bg-stone-200" />
      <div className="h-3 w-11/12 rounded bg-stone-200" />
      <div className="h-3 w-10/12 rounded bg-stone-200" />
      <div className="mt-6 h-3 w-1/4 rounded bg-stone-200" />
      <div className="h-3 w-full rounded bg-stone-200" />
      <div className="h-3 w-9/12 rounded bg-stone-200" />
      <div className="mt-6 h-3 w-1/3 rounded bg-stone-200" />
      <div className="h-3 w-10/12 rounded bg-stone-200" />
    </div>
  )
}

export default App
