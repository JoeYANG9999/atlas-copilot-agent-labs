import * as path from "node:path";
import { pathToFileURL } from "node:url";

const DEFAULT_MODEL_ID = "gpt-5.4";
const DEFAULT_TIMEOUT_MS = 20 * 60 * 1000;
const MODEL_LIST_ERROR_MESSAGE = "无法列出模型，请确认环境变量已配置";

interface ClientBootstrap {
  client: CopilotClientLike;
  modelId: string;
}

export type PresentationSource =
  | { kind: "url"; url: string }
  | { kind: "file"; fileName: string; label: string };

interface RunConversionInput {
  source: PresentationSource;
  style: string;
  pages: number;
  sessionDir: string;
}

// Skills 放在仓库根目录 .github/skills：VS Code Chat 和这个 Web 服务读的是同一份 SKILL.md。
export const SKILLS_DIR = process.env.SKILLS_DIR?.trim() || path.resolve(process.cwd(), "..", ".github", "skills");

interface RunConversionOptions {
  onEvent?: (event: CopilotStreamEvent) => void;
}

interface RunConversionResult {
  replyText: string;
  eventLog: string[];
}

export interface CopilotStreamEvent {
  type: string;
  level: "info" | "error" | "delta";
  summary: string;
  data: Record<string, unknown>;
}

interface CopilotClientOptionsLike {
  cliUrl?: string;
  githubToken?: string;
  useLoggedInUser?: boolean;
}

interface PermissionRequestResultLike {
  kind: "approve-once";
}

interface SessionEventLike {
  type: string;
  data: Record<string, unknown>;
}

interface UserInputRequestLike {
  question: string;
  choices?: string[];
}

interface CopilotSessionLike {
  on(handler: (event: SessionEventLike) => void): () => void;
  sendAndWait(options: { prompt: string }, timeoutMs?: number): Promise<{ data: { content?: string } } | undefined>;
  destroy(): Promise<void>;
}

interface CopilotClientLike {
  start(): Promise<void>;
  listModels(): Promise<Array<{ id: string; name: string; supportedReasoningEfforts?: string[] }>>;
  createSession(config: {
    model: string;
    workingDirectory: string;
    skillDirectories: string[];
    onPermissionRequest: () => PermissionRequestResultLike;
    onUserInputRequest: (request: UserInputRequestLike) => { answer: string; wasFreeform: boolean };
    streaming: boolean;
  }): Promise<CopilotSessionLike>;
}

let bootstrapPromise: Promise<ClientBootstrap> | null = null;
let sdkModulePromise: Promise<CopilotSdkModule> | null = null;

interface CopilotSdkModule {
  CopilotClient: new (options?: CopilotClientOptionsLike) => CopilotClientLike;
}

export class CopilotInitializationError extends Error {
  readonly userMessage: string;

  constructor(message: string, userMessage: string) {
    super(message);
    this.name = "CopilotInitializationError";
    this.userMessage = userMessage;
  }
}

async function loadCopilotSdk(): Promise<CopilotSdkModule> {
  if (sdkModulePromise) {
    return sdkModulePromise;
  }

  const sdkEntryFile = path.join(process.cwd(), "node_modules", "@github", "copilot-sdk", "dist", "index.js");
  const sdkEntryUrl = pathToFileURL(sdkEntryFile).href;
  sdkModulePromise = import(
    /* webpackIgnore: true */ sdkEntryUrl
  ) as Promise<CopilotSdkModule>;
  return sdkModulePromise;
}

function buildClientOptions(): CopilotClientOptionsLike {
  const cliUrl = process.env.COPILOT_CLI_URL?.trim();
  const githubToken = process.env.COPILOT_GITHUB_TOKEN?.trim();

  return {
    cliUrl: cliUrl || undefined,
    githubToken: githubToken || undefined,
    useLoggedInUser: githubToken ? false : undefined,
  };
}

function chooseModel(requestedModel: string | undefined, availableModels: Array<{ id: string }>): string {
  if (requestedModel && availableModels.some((model) => model.id === requestedModel)) {
    return requestedModel;
  }

  const preferredDefault = availableModels.find((model) => model.id === DEFAULT_MODEL_ID);
  return preferredDefault?.id ?? availableModels[0]?.id ?? requestedModel ?? DEFAULT_MODEL_ID;
}

function formatModelLogLine(model: {
  id: string;
  name: string;
  supportedReasoningEfforts?: string[];
}): string {
  const reasoning = model.supportedReasoningEfforts?.length
    ? ` | reasoning: ${model.supportedReasoningEfforts.join(", ")}`
    : "";
  return `- ${model.id} | ${model.name}${reasoning}`;
}

async function bootstrapClient(): Promise<ClientBootstrap> {
  if (bootstrapPromise) {
    return bootstrapPromise;
  }

  bootstrapPromise = (async () => {
    // pptx skill 的脚本放在仓库根目录 .github/skills 下，require('playwright') 等依赖时
    // 会从那里往上找 node_modules，找不到本项目装的包；通过 NODE_PATH 把本项目的 node_modules 带给子进程。
    const localModules = path.join(process.cwd(), "node_modules");
    if (!(process.env.NODE_PATH ?? "").split(path.delimiter).includes(localModules)) {
      process.env.NODE_PATH = [localModules, process.env.NODE_PATH].filter(Boolean).join(path.delimiter);
    }

    const { CopilotClient } = await loadCopilotSdk();
    const client = new CopilotClient(buildClientOptions());
    await client.start();

    let modelId = process.env.COPILOT_MODEL?.trim() || DEFAULT_MODEL_ID;

    try {
      const models = await client.listModels();
      console.log("Available Copilot models:");
      for (const model of models) {
        console.log(formatModelLogLine(model));
      }
      modelId = chooseModel(process.env.COPILOT_MODEL?.trim(), models);
      console.log(`Selected model: ${modelId}`);
    } catch (error) {
      console.warn("Failed to list Copilot models during initialization.", error);
      throw new CopilotInitializationError(
        error instanceof Error ? error.message : "Failed to list Copilot models during initialization.",
        MODEL_LIST_ERROR_MESSAGE,
      );
    }

    return { client, modelId };
  })();

  // 初始化失败（例如还没配置 token）时不缓存失败结果，配置好后下一次请求即可重试
  bootstrapPromise.catch(() => {
    bootstrapPromise = null;
  });

  return bootstrapPromise;
}

function buildPrompt(input: RunConversionInput): string {
  const source =
    input.source.kind === "url"
      ? `素材：url=${input.source.url}`
      : `素材：file=${input.source.fileName}（当前工作目录下，内容是${input.source.label}，直接读取，不需要联网）`;
  return [
    "请使用 knowledge2ppt skill，把素材总结成一份汇报 PPT。",
    `${source}，pages=${input.pages}。`,
    `视觉风格为：${input.style}，不需要再询问风格。`,
    "生成完成后，请明确输出的 PPTX 文件名及写入路径。",
  ].join("\n");
}

function shouldAnswerStyleQuestion(question: string): boolean {
  return /风格|style|visual/i.test(question);
}

function toRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }

  return {};
}

function createStreamEvent(
  type: string,
  level: CopilotStreamEvent["level"],
  summary: string,
  data: Record<string, unknown>,
): CopilotStreamEvent {
  return {
    type,
    level,
    summary,
    data,
  };
}

function formatStreamEvent(event: SessionEventLike): CopilotStreamEvent | null {
  const data = toRecord(event.data);

  switch (event.type) {
    case "assistant.message_delta": {
      const delta = typeof data.deltaContent === "string" ? data.deltaContent : "";
      if (!delta) {
        return null;
      }

      return createStreamEvent(event.type, "delta", delta, { deltaContent: delta });
    }
    case "assistant.message": {
      const content = typeof data.content === "string" ? data.content.trim() : "";
      return createStreamEvent(event.type, "info", content || "Assistant returned a final response.", data);
    }
    case "session.start":
      return createStreamEvent(
        event.type,
        "info",
        `Session started with model ${String(data.selectedModel ?? "unknown")}.`,
        data,
      );
    case "session.resume":
      return createStreamEvent(event.type, "info", `Session resumed with ${String(data.eventCount ?? 0)} prior events.`, data);
    case "session.info":
      return createStreamEvent(event.type, "info", String(data.message ?? "Session info."), data);
    case "session.model_change":
      return createStreamEvent(
        event.type,
        "info",
        `Model changed from ${String(data.previousModel ?? "unknown")} to ${String(data.newModel ?? "unknown")}.`,
        data,
      );
    case "session.handoff":
      return createStreamEvent(event.type, "info", `Session handed off to ${String(data.sourceType ?? "another source")}.`, data);
    case "session.truncation":
      return createStreamEvent(event.type, "info", "Session context was truncated to fit token limits.", data);
    case "session.snapshot_rewind":
      return createStreamEvent(event.type, "info", "Session snapshot was rewound.", data);
    case "session.shutdown":
      return createStreamEvent(event.type, "info", `Session shutdown (${String(data.shutdownType ?? "routine")}).`, data);
    case "session.usage_info":
      return createStreamEvent(event.type, "info", "Session usage info updated.", data);
    case "session.compaction_start":
      return createStreamEvent(event.type, "info", "Session compaction started.", data);
    case "session.compaction_complete":
      return createStreamEvent(event.type, "info", "Session compaction completed.", data);
    case "session.error":
      return createStreamEvent(event.type, "error", String(data.message ?? "Session error."), data);
    case "abort":
      return createStreamEvent(event.type, "error", String(data.reason ?? "Session aborted."), data);
    case "assistant.turn_start":
      return createStreamEvent(event.type, "info", "Assistant turn started.", data);
    case "assistant.turn_end":
      return createStreamEvent(event.type, "info", "Assistant turn ended.", data);
    case "assistant.intent":
      return createStreamEvent(event.type, "info", `Assistant intent: ${String(data.intent ?? "unknown")}.`, data);
    case "assistant.reasoning":
      return createStreamEvent(event.type, "info", String(data.content ?? "Assistant reasoning updated."), data);
    case "assistant.usage":
      return createStreamEvent(event.type, "info", `Assistant usage for ${String(data.model ?? "model")}.`, data);
    case "user.message":
      return createStreamEvent(event.type, "info", String(data.content ?? "User message sent."), data);
    case "tool.user_requested":
      return createStreamEvent(event.type, "info", `Tool requested: ${String(data.toolName ?? "unknown")}.`, data);
    case "tool.execution_start":
      return createStreamEvent(event.type, "info", `Tool started: ${String(data.toolName ?? "unknown")}.`, data);
    case "tool.execution_progress":
      return createStreamEvent(event.type, "info", String(data.progressMessage ?? "Tool is running."), data);
    case "tool.execution_partial_result":
      return createStreamEvent(event.type, "info", String(data.partialOutput ?? "Tool returned partial output."), data);
    case "tool.execution_complete":
      return createStreamEvent(
        event.type,
        data.success ? "info" : "error",
        data.success
          ? `Tool completed: ${String(data.toolName ?? data.toolCallId ?? "unknown")}.`
          : `Tool failed: ${String(toRecord(data.error).message ?? "unknown error")}`,
        data,
      );
    case "skill.invoked":
      return createStreamEvent(event.type, "info", `Skill invoked: ${String(data.name ?? "unknown")}.`, data);
    case "subagent.selected":
      return createStreamEvent(event.type, "info", `Subagent selected: ${String(data.agentDisplayName ?? data.agentName ?? "unknown")}.`, data);
    case "subagent.started":
      return createStreamEvent(event.type, "info", `Subagent started: ${String(data.agentDisplayName ?? data.agentName ?? "unknown")}.`, data);
    case "subagent.completed":
      return createStreamEvent(event.type, "info", `Subagent completed: ${String(data.agentName ?? "unknown")}.`, data);
    case "subagent.failed":
      return createStreamEvent(event.type, "error", `Subagent failed: ${String(data.agentName ?? "unknown")}.`, data);
    case "hook.start":
      return createStreamEvent(event.type, "info", `Hook started: ${String(data.hookType ?? "unknown")}.`, data);
    case "hook.end":
      return createStreamEvent(
        event.type,
        data.success ? "info" : "error",
        data.success
          ? `Hook completed: ${String(data.hookType ?? "unknown")}.`
          : `Hook failed: ${String(toRecord(data.error).message ?? "unknown error")}`,
        data,
      );
    case "system.message":
      return createStreamEvent(event.type, "info", String(data.content ?? "System message."), data);
    default:
      return createStreamEvent(event.type, "info", `Event received: ${event.type}.`, data);
  }
}

function recordEvent(eventLog: string[], event: SessionEventLike): void {
  switch (event.type) {
    case "subagent.selected":
      eventLog.push(`subagent.selected:${String(event.data.agentName ?? "unknown")}`);
      break;
    case "subagent.started":
      eventLog.push(`subagent.started:${String(event.data.agentName ?? "unknown")}`);
      break;
    case "subagent.completed":
      eventLog.push(`subagent.completed:${String(event.data.agentName ?? "unknown")}`);
      break;
    case "tool.execution_start":
      eventLog.push(`tool.start:${String(event.data.toolName ?? "unknown")}`);
      break;
    case "tool.execution_complete":
      eventLog.push(`tool.complete:${String(event.data.toolCallId ?? "unknown")}:${event.data.success ? "ok" : "fail"}`);
      break;
    case "assistant.message_delta":
      if (typeof event.data.deltaContent === "string") {
        eventLog.push(`delta:${event.data.deltaContent.slice(0, 80)}`);
      }
      break;
    case "session.error":
      eventLog.push(`session.error:${String(event.data.message ?? "unknown")}`);
      break;
  }
}

export async function runKnowledgeToPpt(
  input: RunConversionInput,
  options: RunConversionOptions = {},
): Promise<RunConversionResult> {
  const { client, modelId } = await bootstrapClient();
  const timeoutMs = DEFAULT_TIMEOUT_MS;
  const eventLog: string[] = [];
  // Copilot CLI 1.0.43 起权限回复只认 approve-once / approve-for-session / reject 等写法；
  // SDK 0.2.2 自带的 approveAll 仍返回旧的 { kind: "approved" }，每次工具调用都会报「unexpected user permission response」。
  const approveAll = (): PermissionRequestResultLike => ({ kind: "approve-once" });

  const session = await client.createSession({
    model: modelId,
    workingDirectory: input.sessionDir,
    skillDirectories: [SKILLS_DIR],
    onPermissionRequest: approveAll,
    onUserInputRequest: (request: UserInputRequestLike) => {
      const answer = shouldAnswerStyleQuestion(request.question)
        ? input.style
        : request.choices?.[0] ?? input.style;

      return {
        answer,
        wasFreeform: !(request.choices ?? []).includes(answer),
      };
    },
    streaming: true,
  });

  const unsubscribe = session.on((event: SessionEventLike) => {
    recordEvent(eventLog, event);
    options.onEvent?.(formatStreamEvent(event) ?? createStreamEvent(event.type, "info", `Event received: ${event.type}.`, toRecord(event.data)));
  });

  try {
    const prompt = buildPrompt(input);
    console.log("Copilot 提示词:\n" + prompt);
    const reply = await session.sendAndWait({ prompt }, timeoutMs);
    return {
      replyText: reply?.data.content ?? "",
      eventLog,
    };
  } finally {
    unsubscribe();
    await session.destroy();
  }
}