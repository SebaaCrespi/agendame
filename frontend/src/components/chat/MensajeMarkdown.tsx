import { Fragment, type ReactNode } from 'react';

/**
 * Markdown mínimo para las respuestas del asistente: párrafos, listas,
 * tablas con pipes, **negrita** y `código`. Todo se renderiza como texto
 * (sin HTML crudo), así que no hay riesgo de inyección.
 */
export function MensajeMarkdown({ texto }: { texto: string }) {
  const lineas = texto.replace(/\r\n/g, '\n').split('\n');
  const bloques: ReactNode[] = [];
  let i = 0;

  while (i < lineas.length) {
    const linea = lineas[i];

    // Tabla: fila con pipes seguida de separador |---|
    if (esFilaTabla(linea) && i + 1 < lineas.length && /^\s*\|?\s*:?-{2,}/.test(lineas[i + 1])) {
      const cabecera = celdas(linea);
      const filas: string[][] = [];
      i += 2;
      while (i < lineas.length && esFilaTabla(lineas[i])) filas.push(celdas(lineas[i++]));
      bloques.push(
        <div key={bloques.length} className="-mx-1 overflow-x-auto">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-line">
                {cabecera.map((c, j) => (
                  <th key={j} className="px-1 py-1 font-semibold">{inline(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filas.map((f, k) => (
                <tr key={k} className="border-b border-line last:border-0">
                  {f.map((c, j) => (
                    <td key={j} className="px-1 py-1 align-top">{inline(c)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // Lista con viñetas o numerada
    if (/^\s*([-*•]|\d+[.)])\s+/.test(linea)) {
      const ordenada = /^\s*\d+[.)]/.test(linea);
      const items: string[] = [];
      while (i < lineas.length && /^\s*([-*•]|\d+[.)])\s+/.test(lineas[i])) {
        items.push(lineas[i++].replace(/^\s*([-*•]|\d+[.)])\s+/, ''));
      }
      const Lista = ordenada ? 'ol' : 'ul';
      bloques.push(
        <Lista key={bloques.length} className={ordenada ? 'list-decimal space-y-0.5 pl-5' : 'list-disc space-y-0.5 pl-5'}>
          {items.map((it, k) => (
            <li key={k}>{inline(it)}</li>
          ))}
        </Lista>
      );
      continue;
    }

    if (!linea.trim()) {
      i++;
      continue;
    }

    // Párrafo: líneas seguidas hasta una vacía u otro bloque
    const parrafo: string[] = [];
    while (i < lineas.length && lineas[i].trim() && !esFilaTabla(lineas[i]) && !/^\s*([-*•]|\d+[.)])\s+/.test(lineas[i])) {
      parrafo.push(lineas[i++].replace(/^#+\s*/, ''));
    }
    bloques.push(
      <p key={bloques.length}>
        {parrafo.map((p, k) => (
          <Fragment key={k}>
            {k > 0 && <br />}
            {inline(p)}
          </Fragment>
        ))}
      </p>
    );
  }

  return <div className="space-y-2">{bloques}</div>;
}

const esFilaTabla = (l: string) => /^\s*\|.*\|\s*$/.test(l);

const celdas = (l: string) =>
  l
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((c) => c.trim());

/** **negrita** y `código` dentro de una línea. */
function inline(texto: string): ReactNode {
  return texto.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((parte, k) => {
    if (parte.startsWith('**') && parte.endsWith('**')) return <strong key={k} className="font-semibold">{parte.slice(2, -2)}</strong>;
    if (parte.startsWith('`') && parte.endsWith('`')) return <code key={k} className="rounded bg-surface-2 px-1 text-[12px]">{parte.slice(1, -1)}</code>;
    return parte;
  });
}
