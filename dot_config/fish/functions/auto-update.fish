# =============================================================================
# auto-update.fish — 一键更新（开代理 + 全量更新）
# =============================================================================
# Description : 薄包装：onproxy 后委托 update-all（两者均按名从 functions/
#               惰性加载，首次调用时才 source）。由原 conf.d/00_aliases.fish
#               迁入；独立成文件是 fish autoload 按文件名解析的要求。
# Usage       : auto-update（无参即 update-all 全量）
# Guards      : onproxy 仅在函数存在时调用（functions/ 缺失时不报错）；
#               实际更新由 update-all 逐项 type -q 守卫
# Author      : Payne
# =============================================================================
function auto-update --description "一键更新所有开发环境 (fish 版)"
    onproxy
    update-all
end
