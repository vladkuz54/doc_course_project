"use client";

export type StopAddress = { street: string; number: string; city: string };

export const EMPTY_STOP: StopAddress = { street: "", number: "", city: "" };

export function joinAddress({ street, number, city }: StopAddress) {
  return `${city.trim()}, ${street.trim()} ${number.trim()}`;
}

export function splitAddress(address: string): StopAddress {
  const match = /^(.+?), (.+) (\S+)$/.exec(address);
  if (!match) return { ...EMPTY_STOP, street: address };
  const [, city, street, number] = match;
  return { street, number, city };
}

const FIELDS: { key: keyof StopAddress; label: string }[] = [
  { key: "street", label: "Street" },
  { key: "number", label: "Number" },
  { key: "city", label: "City" },
];

export function StopFields({
  stops,
  onChange,
}: {
  stops: StopAddress[];
  onChange: (stops: StopAddress[]) => void;
}) {
  const edit = (index: number, key: keyof StopAddress, value: string) => {
    onChange(
      stops.map((stop, i) => (i === index ? { ...stop, [key]: value } : stop)),
    );
  };

  const move = (from: number, to: number) => {
    const next = [...stops];
    next.splice(to, 0, next.splice(from, 1)[0]);
    onChange(next);
  };

  return (
    <fieldset className="wide stop-fields">
      <legend>Stops</legend>
      <ol>
        {stops.map((stop, index) => (
          <li key={index}>
            {FIELDS.map(({ key, label }) => (
              <label key={key} className={`stop-${key}`}>
                {label}
                <input
                  aria-label={`Stop ${index + 1} ${label.toLowerCase()}`}
                  value={stop[key]}
                  pattern=".*\S.*"
                  title={`Enter the ${label.toLowerCase()}`}
                  required
                  onChange={(event) => edit(index, key, event.target.value)}
                />
              </label>
            ))}
            <button
              type="button"
              className="secondary"
              disabled={index === 0}
              onClick={() => move(index, index - 1)}
            >
              Up
            </button>
            <button
              type="button"
              className="secondary"
              disabled={index === stops.length - 1}
              onClick={() => move(index, index + 1)}
            >
              Down
            </button>
            <button
              type="button"
              className="secondary danger"
              disabled={stops.length === 1}
              onClick={() => onChange(stops.filter((_, i) => i !== index))}
            >
              Remove
            </button>
          </li>
        ))}
      </ol>
      <button
        type="button"
        className="secondary"
        onClick={() => onChange([...stops, EMPTY_STOP])}
      >
        Add stop
      </button>
    </fieldset>
  );
}
