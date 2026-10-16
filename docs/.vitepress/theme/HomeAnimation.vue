<script setup lang="ts">
import { nextTick, onMounted, watch } from "vue";
import { useData, useRoute } from "vitepress";
import { animate, inView, stagger } from "motion-v";

const { frontmatter } = useData();
const route = useRoute();

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

async function run() {
  if (frontmatter.value.layout !== "home" || prefersReducedMotion()) return;
  await nextTick();

  const heroText = document.querySelectorAll(
    ".VPHero .name, .VPHero .text, .VPHero .tagline, .VPHero .actions"
  );
  if (heroText.length) {
    animate(
      heroText,
      { opacity: [0, 1], y: [24, 0] },
      { duration: 0.6, delay: stagger(0.12), ease: "easeOut" }
    );
  }

  const heroImage = document.querySelector(".VPHero .image-container");
  if (heroImage) {
    animate(
      heroImage,
      { opacity: [0, 1], scale: [0.9, 1] },
      { duration: 0.8, delay: 0.2, ease: "easeOut" }
    );
  }

  const features = document.querySelectorAll(".VPFeatures .item");
  features.forEach((el) => ((el as HTMLElement).style.opacity = "0"));
  inView(
    ".VPFeatures",
    () => {
      animate(
        features,
        { opacity: [0, 1], y: [32, 0] },
        { duration: 0.5, delay: stagger(0.1), ease: "easeOut" }
      );
    },
    { amount: 0.2 }
  );
}

onMounted(run);
watch(() => route.path, run);
</script>

<template>
  <span hidden />
</template>
