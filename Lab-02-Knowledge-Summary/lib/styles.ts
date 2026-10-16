export type PresentationStyleId = "geek" | "consulting" | "magazine" | "brand";

export const DEFAULT_PAGES = 6;
export const MIN_PAGES = 1;
export const MAX_PAGES = 30;

export const PRESENTATION_STYLES = [
  {
    id: "geek",
    label: "极客风",
    shortLabel: "Geek",
    description: "冷静留白、网格感强、技术文档气质，适合情报简报、产品说明、技术分享。",
    emphasis: "偏技术、偏结构化、表达克制。",
    previewClassName: "geek",
  },
  {
    id: "consulting",
    label: "咨询风",
    shortLabel: "Consulting",
    description: "黑白灰或低饱和商务配色、标题突出、结构严整，适合管理层汇报。",
    emphasis: "默认推荐，商务文档感更强。",
    previewClassName: "consulting",
  },
  {
    id: "magazine",
    label: "杂志风",
    shortLabel: "Magazine",
    description: "版式感更强、报刊式分栏、保留留白与节奏，适合内容型页面转述。",
    emphasis: "更强调视觉节奏与阅读体验。",
    previewClassName: "magazine",
  },
  {
    id: "brand",
    label: "公司品牌风",
    shortLabel: "Brand",
    description: "白底，主色深蓝 #003A70，强调色亮黄 #FFC20E，标题加粗，每页底部一条深蓝细条。",
    emphasis: "统一公司品牌视觉：所有页面白底，深蓝主色配亮黄强调色，标题加粗，每页底部固定一条深蓝 #003A70 细条。",
    previewClassName: "brand",
  },
];

export function getPresentationStyle(styleId: string): (typeof PRESENTATION_STYLES)[number] | undefined {
  return PRESENTATION_STYLES.find((style) => style.id === styleId);
}

export function parsePageCount(value: number | string | undefined): number | null {
  if (typeof value === "number" && Number.isInteger(value)) {
    return value >= MIN_PAGES && value <= MAX_PAGES ? value : null;
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) {
      return null;
    }

    const parsed = Number(trimmed);
    if (!Number.isInteger(parsed)) {
      return null;
    }

    return parsed >= MIN_PAGES && parsed <= MAX_PAGES ? parsed : null;
  }

  return null;
}