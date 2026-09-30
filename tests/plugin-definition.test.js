import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

const ROOT = resolve(import.meta.dirname, '..');
const PLUGIN_DIR = resolve(ROOT, 'plugins/company');
const SKILL_DIR = resolve(PLUGIN_DIR, 'skills/company');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf-8'));
}

function readText(filePath) {
  return readFileSync(filePath, 'utf-8');
}

/**
 * Parse YAML-style front-matter from a Markdown file.
 * Returns an object with { attributes, body }.
 */
function parseFrontMatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return { attributes: {}, body: content };

  const raw = match[1];
  const attributes = {};
  for (const line of raw.split('\n')) {
    // Handle simple "key: value" and multi-line "> value"
    const kv = line.match(/^(\w[\w-]*):\s*(.*)/);
    if (kv) {
      let val = kv[2].trim();
      // Strip surrounding quotes
      if ((val.startsWith('"') && val.endsWith('"')) ||
          (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      attributes[kv[1]] = val;
    }
  }
  const body = content.slice(match[0].length).trim();
  return { attributes, body };
}

// ---------------------------------------------------------------------------
// 1. plugin.json validation
// ---------------------------------------------------------------------------

describe('plugin.json', () => {
  const pluginJsonPath = resolve(PLUGIN_DIR, '.claude-plugin/plugin.json');

  it('should exist', () => {
    expect(existsSync(pluginJsonPath)).toBe(true);
  });

  it('should be valid JSON', () => {
    expect(() => readJson(pluginJsonPath)).not.toThrow();
  });

  it('should have required fields: name, description, version', () => {
    const data = readJson(pluginJsonPath);
    expect(data).toHaveProperty('name');
    expect(data).toHaveProperty('description');
    expect(data).toHaveProperty('version');
  });

  it('name should be a non-empty string', () => {
    const data = readJson(pluginJsonPath);
    expect(typeof data.name).toBe('string');
    expect(data.name.length).toBeGreaterThan(0);
  });

  it('version should follow semver pattern', () => {
    const data = readJson(pluginJsonPath);
    expect(data.version).toMatch(/^\d+\.\d+\.\d+/);
  });
});

// ---------------------------------------------------------------------------
// 2. SKILL.md validation
// ---------------------------------------------------------------------------

describe('SKILL.md', () => {
  const skillPath = resolve(SKILL_DIR, 'SKILL.md');

  it('should exist', () => {
    expect(existsSync(skillPath)).toBe(true);
  });

  it('should have YAML front-matter', () => {
    const content = readText(skillPath);
    expect(content).toMatch(/^---\r?\n/);
  });

  it('front-matter should contain required fields: name, description, trigger', () => {
    const content = readText(skillPath);
    const { attributes } = parseFrontMatter(content);
    expect(attributes).toHaveProperty('name');
    expect(attributes).toHaveProperty('description');
    expect(attributes).toHaveProperty('trigger');
  });

  it('trigger should start with /', () => {
    const content = readText(skillPath);
    const { attributes } = parseFrontMatter(content);
    expect(attributes.trigger).toMatch(/^\//);
  });

  it('body should contain workflow sections', () => {
    const content = readText(skillPath);
    expect(content).toContain('## ワークフロー');
    expect(content).toContain('## 運営モード');
  });

  it('body should reference both template files', () => {
    const content = readText(skillPath);
    expect(content).toContain('references/departments.md');
    expect(content).toContain('references/claude-md-template.md');
  });
});

// ---------------------------------------------------------------------------
// 3. references/departments.md validation
// ---------------------------------------------------------------------------

describe('references/departments.md', () => {
  const deptPath = resolve(SKILL_DIR, 'references/departments.md');

  it('should exist', () => {
    expect(existsSync(deptPath)).toBe(true);
  });

  const EXPECTED_DEPARTMENTS = [
    '秘書室',
    'PM',
    'リサーチ',
    'マーケティング',
    '開発',
    '経理',
    '営業',
    'クリエイティブ',
    '人事',
  ];

  it.each(EXPECTED_DEPARTMENTS)(
    'should contain department section: %s',
    (dept) => {
      const content = readText(deptPath);
      expect(content).toContain(dept);
    }
  );

  it('should contain CLAUDE.md templates for all departments', () => {
    const content = readText(deptPath);
    const claudeMdSections = [
      'secretary/CLAUDE.md',
      'pm/CLAUDE.md',
      'research/CLAUDE.md',
      'marketing/CLAUDE.md',
      'engineering/CLAUDE.md',
      'finance/CLAUDE.md',
      'sales/CLAUDE.md',
      'creative/CLAUDE.md',
      'hr/CLAUDE.md',
    ];
    for (const section of claudeMdSections) {
      expect(content).toContain(section);
    }
  });

  it('each department template should have a _template.md code block', () => {
    const content = readText(deptPath);
    // Each department section has at least one template with front-matter
    // containing "type:" or "date:" or "created:"
    const templateBlocks = content.match(/```markdown[\s\S]*?```/g) || [];
    expect(templateBlocks.length).toBeGreaterThanOrEqual(EXPECTED_DEPARTMENTS.length);
  });

  it('templates should use {{YYYY-MM-DD}} date placeholder consistently', () => {
    const content = readText(deptPath);
    const templateBlocks = content.match(/```markdown[\s\S]*?```/g) || [];
    const blocksWithDate = templateBlocks.filter(b => b.includes('date:') || b.includes('created:'));
    for (const block of blocksWithDate) {
      expect(block).toContain('{{YYYY-MM-DD}}');
    }
  });
});

// ---------------------------------------------------------------------------
// 4. references/claude-md-template.md validation
// ---------------------------------------------------------------------------

describe('references/claude-md-template.md', () => {
  const templatePath = resolve(SKILL_DIR, 'references/claude-md-template.md');

  it('should exist', () => {
    expect(existsSync(templatePath)).toBe(true);
  });

  const REQUIRED_VARIABLES = [
    '{{BUSINESS_TYPE}}',
    '{{GOALS_AND_CHALLENGES}}',
    '{{CREATED_DATE}}',
    '{{ADDITIONAL_DEPARTMENTS}}',
    '{{DEPARTMENT_TABLE_ROWS}}',
    '{{PERSONALIZATION_NOTES}}',
  ];

  it.each(REQUIRED_VARIABLES)(
    'should contain template variable: %s',
    (variable) => {
      const content = readText(templatePath);
      expect(content).toContain(variable);
    }
  );

  it('should contain variable reference table', () => {
    const content = readText(templatePath);
    expect(content).toContain('## 変数リファレンス');
  });

  it('variable reference table should document all required variables', () => {
    const content = readText(templatePath);
    for (const variable of REQUIRED_VARIABLES) {
      // Each variable should be referenced in the documentation as well as in the template
      const escaped = variable.replace(/[{}]/g, '\\$&');
      const matches = content.match(new RegExp(escaped, 'g')) || [];
      expect(matches.length).toBeGreaterThanOrEqual(2); // at least in template + reference table
    }
  });

  it('template should contain organization structure section', () => {
    const content = readText(templatePath);
    expect(content).toContain('## 組織構成');
  });

  it('template should contain operation rules section', () => {
    const content = readText(templatePath);
    expect(content).toContain('## 運営ルール');
  });
});

// ---------------------------------------------------------------------------
// 5. File structure integrity
// ---------------------------------------------------------------------------

describe('plugin directory structure', () => {
  const requiredFiles = [
    'plugins/company/.claude-plugin/plugin.json',
    'plugins/company/skills/company/SKILL.md',
    'plugins/company/skills/company/references/departments.md',
    'plugins/company/skills/company/references/claude-md-template.md',
  ];

  it.each(requiredFiles)(
    'required file should exist: %s',
    (file) => {
      expect(existsSync(resolve(ROOT, file))).toBe(true);
    }
  );

  it('plugin name in plugin.json should match skill name in SKILL.md', () => {
    const pluginData = readJson(resolve(PLUGIN_DIR, '.claude-plugin/plugin.json'));
    const skillContent = readText(resolve(SKILL_DIR, 'SKILL.md'));
    const { attributes } = parseFrontMatter(skillContent);
    expect(pluginData.name).toBe(attributes.name);
  });
});

// ---------------------------------------------------------------------------
// 6. Connections (2026-10: 公式の連携を正にした作り直し)
// ---------------------------------------------------------------------------

describe('connections guide', () => {
  const skill = () => readText(resolve(SKILL_DIR, 'SKILL.md'));
  const guide = () => readText(resolve(SKILL_DIR, 'references/connections.md'));

  it.each([
    'references/connections.md',
    'references/connections-legacy.md',
    'scripts/mail_readonly.py',
    'scripts/caldav_readonly.py',
    'scripts/outlook_calendar_win.ps1',
    'scripts/mac_calendar.applescript',
  ])('file should exist: %s', (file) => {
    expect(existsSync(resolve(SKILL_DIR, file))).toBe(true);
  });

  it('onboarding asks for the email address instead of "Google or Microsoft"', () => {
    const s = skill();
    expect(s).toContain('#### Q3: お仕事のメールアドレス');
    expect(s).toContain('nslookup -type=mx');
    expect(s).not.toContain('googleBased');
    expect(s).not.toContain('microsoftBased');
  });

  it('onboarding asks Windows or Mac', () => {
    expect(skill()).toContain('#### Q4: パソコン');
  });

  it('old Google Cloud / Azure steps are no longer in SKILL.md (moved to legacy)', () => {
    const s = skill();
    expect(s).not.toContain('Google Cloud Console でプロジェクト作成');
    expect(s).not.toContain('Azure Portal でアプリ登録');
    expect(readText(resolve(SKILL_DIR, 'references/connections-legacy.md'))).toContain('Google Cloud Console でプロジェクト作成');
  });

  it('SKILL.md references the connections guide and has 連携チェック', () => {
    const s = skill();
    expect(s).toContain('references/connections.md');
    expect(s).toContain('### 連携チェック');
  });

  it('guide covers every route decided with the owner', () => {
    const g = guide();
    for (const heading of [
      '## §1. メールアドレスから種類を見分ける',
      '### §2-A. Microsoft 365',
      '### §2-B. Google',
      '### 3-2. 🔴「受け取るとサーバーから消える」設定',
      '### 3-3. サーバーの ID・パスワードが分からない人',
      '### 3-4. Yahoo メール',
      '### 3-5. 個人の Outlook.com・Hotmail',
      '## §4. カレンダー',
      '## §5. フォルダ',
      '## §6. 社内チャット',
      '## §7. 連携チェック',
    ]) {
      expect(g).toContain(heading);
    }
  });

  it('guide forbids pasting passwords into the conversation', () => {
    expect(guide()).toContain('パスワードを会話に貼らせない');
  });
});

// ---------------------------------------------------------------------------
// 7. Organization rules (2026-10: 手順書を部署に置く絶対ルール)
// ---------------------------------------------------------------------------

describe('organization rules', () => {
  const skill = () => readText(resolve(SKILL_DIR, 'SKILL.md'));
  const org = () => readText(resolve(SKILL_DIR, 'references/organization.md'));

  it('organization.md exists and has the three absolute rules', () => {
    const o = org();
    expect(o).toContain('### ルール1: 同じ作業が2回目に来たら、必ず手順書にしようと提案する');
    expect(o).toContain('### ルール2: 手順書は必ずどこかの部署に置く');
    expect(o).toContain('### ルール3: 手順書には必ず連携先を書き、連携表に1行足す');
    expect(o).toContain('## §6. 組織の健康診断');
  });

  it('SKILL.md states the absolute rules in operating mode and routes by manuals first', () => {
    const s = skill();
    expect(s).toContain('### 🔴 組織の絶対ルール（手順書・部署・連携表）');
    expect(s).toContain('references/organization.md');
    expect(s).toContain('manuals/INDEX.md');
    expect(s).toContain('.company/flow-map.md');
    expect(s).toContain('secretary/work-log.md');
  });

  it('departments.md requires manuals/ in every department', () => {
    expect(readText(resolve(SKILL_DIR, 'references/departments.md'))).toContain('`manuals/` サブフォルダ（手順書）');
  });

  it('claude-md-template carries the absolute rules', () => {
    expect(readText(resolve(SKILL_DIR, 'references/claude-md-template.md'))).toContain('組織の絶対ルール');
  });
});

describe('organization rules: no stale instructions', () => {
  const dep = () => readText(resolve(SKILL_DIR, 'references/departments.md'));

  it('stale "department at 2 similar tasks / create immediately / save to notes" rules are gone', () => {
    const files = [
      resolve(SKILL_DIR, 'references/departments.md'),
      resolve(SKILL_DIR, 'references/claude-md-template.md'),
      resolve(ROOT, 'README.md'),
    ];
    for (const f of files) {
      const c = readText(f);
      expect(c).not.toContain('同じ領域のタスクが2回以上繰り返されたら、部署作成を提案する');
      expect(c).not.toContain('ユーザーが明示的に依頼した場合は即座に作成する');
      expect(c).not.toContain('該当部署が未作成の場合は secretary/notes/ に保存する');
      expect(c).not.toContain('同領域のタスクが2回以上 → 部署作成を提案');
    }
  });

  it('every subfolder list in department templates includes manuals/', () => {
    const blocks = dep().split('## サブフォルダ\n').slice(1);
    expect(blocks.length).toBeGreaterThan(5);
    for (const b of blocks) {
      expect(b.split('```')[0]).toContain('`manuals/`');
    }
  });

  it('every department CLAUDE.md template tells to read manuals/INDEX.md first', () => {
    const d = dep();
    const deptSections = d.split(/\n## (?=\w+\/CLAUDE\.md)/).slice(1).filter((x) => !x.startsWith('secretary/'));
    expect(deptSections.length).toBeGreaterThan(5);
    for (const sec of deptSections) {
      expect(sec).toContain('manuals/INDEX.md');
    }
  });

  it('auto-chaining has safety stops', () => {
    const o = readText(resolve(SKILL_DIR, 'references/organization.md'));
    expect(o).toContain('自動でつなぐのは、1回の依頼につき1段まで');
    expect(o).toContain('外に出る操作は、連携表や手順書の書き方にかかわらず、毎回受講者の「送って」「やって」をもらう');
    expect(o).toContain('同じ部署の同じ手順書に2回来たら止める');
  });

  it('every references/ file mentioned in SKILL.md exists', () => {
    const s = readText(resolve(SKILL_DIR, 'SKILL.md'));
    const refs = [...new Set(s.match(/references\/[\w-]+\.md/g))];
    expect(refs.length).toBeGreaterThan(3);
    for (const r of refs) {
      expect(existsSync(resolve(SKILL_DIR, r))).toBe(true);
    }
  });
});
