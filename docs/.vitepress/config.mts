import { defineConfig } from "vitepress";

export default defineConfig({
  title: "bootcamp-company",
  base: "/bootcamp-company/",
  cleanUrls: true,
  ignoreDeadLinks: [/^http:\/\/localhost/],

  head: [["link", { rel: "icon", type: "image/png", href: "/bootcamp-company/hero-image.png" }]],

  locales: {
    root: {
      label: "日本語",
      lang: "ja",
      description: "Claude Code で仮想組織を構築・運営するプラグイン",
      themeConfig: {
        nav: [
          { text: "ガイド", link: "/guide/getting-started" },
          { text: "リファレンス", link: "/reference/departments" },
          {
            text: "GitHub",
            link: "https://github.com/inoshinichi/bootcamp-company",
          },
        ],
        sidebar: {
          "/guide/": [
            {
              text: "はじめに",
              items: [
                { text: "cc-company とは", link: "/guide/what-is-cc-company" },
                { text: "クイックスタート", link: "/guide/getting-started" },
              ],
            },
            {
              text: "使い方",
              items: [
                { text: "秘書との日常", link: "/guide/daily-usage" },
                { text: "部署を追加する", link: "/guide/adding-departments" },
                { text: "ダッシュボード", link: "/guide/dashboard" },
                { text: "研修の前の準備", link: "/guide/junbi" },
                { text: "MCP連携ガイド", link: "/guide/mcp-integration" },
                {
                  text: "v1 からのアップグレード",
                  link: "/guide/migration",
                },
              ],
            },
            {
              text: "事例",
              items: [{ text: "活用事例", link: "/guide/use-cases" }],
            },
          ],
          "/reference/": [
            {
              text: "リファレンス",
              items: [
                { text: "部署一覧", link: "/reference/departments" },
                { text: "ファイル構成", link: "/reference/file-structure" },
              ],
            },
          ],
        },
        outline: {
          label: "目次",
        },
        docFooter: {
          prev: "前のページ",
          next: "次のページ",
        },
      },
    },
    en: {
      label: "English",
      lang: "en",
      description:
        "A plugin to build and run a virtual organization with Claude Code",
      themeConfig: {
        nav: [
          { text: "Guide", link: "/en/guide/getting-started" },
          { text: "Reference", link: "/en/reference/departments" },
          {
            text: "GitHub",
            link: "https://github.com/inoshinichi/bootcamp-company",
          },
        ],
        sidebar: {
          "/en/guide/": [
            {
              text: "Introduction",
              items: [
                {
                  text: "What is cc-company?",
                  link: "/en/guide/what-is-cc-company",
                },
                {
                  text: "Quick Start",
                  link: "/en/guide/getting-started",
                },
              ],
            },
            {
              text: "Usage",
              items: [
                {
                  text: "Daily Usage with Secretary",
                  link: "/en/guide/daily-usage",
                },
                {
                  text: "Adding Departments",
                  link: "/en/guide/adding-departments",
                },
                {
                  text: "Dashboard",
                  link: "/en/guide/dashboard",
                },
                {
                  text: "MCP Integration",
                  link: "/en/guide/mcp-integration",
                },
                {
                  text: "Upgrading from v1",
                  link: "/en/guide/migration",
                },
              ],
            },
            {
              text: "Examples",
              items: [
                { text: "Use Cases", link: "/en/guide/use-cases" },
              ],
            },
          ],
          "/en/reference/": [
            {
              text: "Reference",
              items: [
                {
                  text: "Departments",
                  link: "/en/reference/departments",
                },
                {
                  text: "File Structure",
                  link: "/en/reference/file-structure",
                },
              ],
            },
          ],
        },
        outline: {
          label: "On this page",
        },
        docFooter: {
          prev: "Previous",
          next: "Next",
        },
      },
    },
  },

  themeConfig: {
    socialLinks: [
      { icon: "github", link: "https://github.com/inoshinichi/bootcamp-company" },
    ],

    footer: {
      message:
        'MIT License | Forked from <a href="https://github.com/Shin-sibainu/cc-company" target="_blank">Shin-sibainu/cc-company</a>',
      copyright: "© 2026 inoshinichi（元: Shin-sibainu/cc-company）",
    },

    search: {
      provider: "local",
    },
  },
});
