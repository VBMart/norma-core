const PHRASES = [
  'capturing pixels',
  'recording motion',
  'bottling moments',
  'saving frames',
  'logging dataset',
  'snapshot saved',
  'marking the trail',
  'stamping the moment',
  'grabbing reality',
  'pickling state',
  'memorizing now',
  'eternalizing',
  'engraving timeline',
  'bookmarking pixels',
  'crystallizing data',
  'inking the record',
  'tapping the recorder',
  'curating sample',
  'etching frame',
  'stitching memory',
  'sealing the moment',
  'slicing reality',
  'annotating run',
  'painting bytes',
  'burning to disk',
  'pinning the frame',
  'collecting droplets',
  'archiving the now',
  'tagging trajectory',
  'minting episode',
];

export function randomPhrase(): string {
  return PHRASES[Math.floor(Math.random() * PHRASES.length)];
}

export function formatTagStamp(date: Date = new Date()): string {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  );
}

export function defaultTag(date: Date = new Date()): string {
  return `[${formatTagStamp(date)}]: ${randomPhrase()}`;
}
