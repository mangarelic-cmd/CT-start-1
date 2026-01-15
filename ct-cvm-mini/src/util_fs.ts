import fs from "node:fs";
import path from "node:path";

export const readText = (p: string) => fs.readFileSync(p, "utf8");

export const writeText = (p: string, t: string) => {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, t, "utf8");
};

export const writeJson = (p: string, o: unknown) =>
  writeText(p, JSON.stringify(o, null, 2) + "\n");
