export const GITHUB_REPO_URL = "https://github.com/gghatano/syntheticdata-generation-catalog";
export const REPO_BRANCH = "main";

export function buildBlobUrl(path: string, branch: string = REPO_BRANCH): string {
  const cleanPath = path.replace(/^\/+/, "");
  return `${GITHUB_REPO_URL}/blob/${branch}/${cleanPath}`;
}

export function buildRawUrl(path: string, branch: string = REPO_BRANCH): string {
  const cleanPath = path.replace(/^\/+/, "");
  return `${GITHUB_REPO_URL}/raw/${branch}/${cleanPath}`;
}
