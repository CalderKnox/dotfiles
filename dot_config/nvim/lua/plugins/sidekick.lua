-- Sidekick CLI-only: disable NES so LazyVim does not enable Copilot LSP.
-- Official sidekick.nvim opt; see LazyVim ai.sidekick extra (nes.enabled ~= false gate).
return {
  {
    "folke/sidekick.nvim",
    opts = {
      nes = { enabled = false },
    },
  },
}
