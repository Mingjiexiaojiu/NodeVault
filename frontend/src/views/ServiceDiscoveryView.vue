<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-gray-900">服务发现</h1>
        <p class="text-sm text-gray-400 mt-0.5">输入服务地址，自动发现 OpenAPI 接口并批量导入为 Node</p>
      </div>
    </div>

    <div class="flex gap-8">
      <!-- 左侧步骤导航 -->
      <aside class="w-48 shrink-0">
        <nav class="sticky top-24 space-y-0.5">
          <button
            v-for="(section, i) in sections"
            :key="section.id"
            class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150 text-left"
            :class="currentStep === section.id
              ? 'bg-indigo-50 text-indigo-700 font-semibold'
              : section.done
                ? 'text-emerald-600 hover:bg-emerald-50'
                : 'text-gray-400 cursor-default'"
            :disabled="!section.done && currentStep !== section.id"
            @click="section.done ? currentStep = section.id : null"
          >
            <span
              class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
              :class="currentStep === section.id
                ? 'text-white'
                : section.done
                  ? 'bg-emerald-500 text-white'
                  : 'bg-gray-100 text-gray-400'"
              :style="currentStep === section.id ? 'background: linear-gradient(135deg, #6366f1, #8b5cf6)' : ''"
            >
              <svg v-if="section.done && currentStep !== section.id" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <template v-else>{{ i + 1 }}</template>
            </span>
            <span>{{ section.label }}</span>
          </button>
        </nav>
      </aside>

      <!-- 右侧内容 -->
      <div class="flex-1 min-w-0 space-y-6">

        <!-- ① 探测 -->
        <section v-show="currentStep === 'probe'" class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0" style="background: linear-gradient(135deg, #0891b2, #06b6d4)">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">探测服务</h2>
              <p class="text-xs text-gray-400 mt-0.5">输入基础 URL，自动探测 OpenAPI / Swagger 文档</p>
            </div>
          </div>
          <div class="p-6 space-y-5">
            <!-- URL 输入 -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                服务地址 <span class="text-red-500">*</span>
              </label>
              <div class="flex gap-3">
                <input
                  v-model="baseUrl"
                  placeholder="https://api.example.com"
                  class="flex-1 block rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                  @keyup.enter="handleProbe"
                />
                <button
                  type="button"
                  class="px-5 py-2.5 rounded-xl text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 whitespace-nowrap"
                style="background: linear-gradient(135deg, #6366f1, #8b5cf6); box-shadow: 0 3px 10px rgba(99,102,241,0.25)"
                  :disabled="!baseUrl.trim() || probing"
                  @click="handleProbe"
                >
                  {{ probing ? '探测中...' : '开始探测' }}
                </button>
              </div>
            </div>

            <!-- 探测进度 -->
            <div v-if="probeAttempts.length" class="rounded-xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 2px rgba(0,0,0,0.03)">
              <div class="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">探测路径</div>
              <div class="divide-y divide-gray-100 max-h-60 overflow-y-auto">
                <div
                  v-for="(a, i) in probeAttempts"
                  :key="i"
                  class="flex items-center gap-3 px-4 py-2 text-sm"
                >
                  <span
                    class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                    :class="a.success ? 'bg-green-100 text-green-600' : a.status === 401 ? 'bg-amber-100 text-amber-600' : 'bg-gray-100 text-gray-400'"
                  >
                    <template v-if="a.success">✓</template>
                    <template v-else-if="a.status === 401">!</template>
                    <template v-else>✗</template>
                  </span>
                  <span class="font-mono text-gray-600 flex-1 truncate">{{ a.path }}</span>
                  <span class="text-xs" :class="a.success ? 'text-green-600' : a.status === 401 ? 'text-amber-500' : 'text-gray-400'">
                    {{ a.status ?? '--' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 需要认证提示 -->
            <div v-if="needsAuth && !probeDrafts.length" class="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-3">
              <p class="text-sm text-amber-700 font-medium">⚠ 服务需要认证才能访问 OpenAPI 文档</p>
              <button
                type="button"
                class="px-4 py-2 rounded-xl bg-amber-600 text-white text-sm font-medium hover:bg-amber-700 transition-colors"
                @click="showAuthModal = true"
              >
                配置认证
              </button>
            </div>

            <!-- 探测失败兜底 -->
            <div v-if="probeFailed" class="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3">
              <div v-if="probeErrorType" class="flex items-center gap-2 text-sm text-gray-600">
                <span v-if="probeErrorType === 'dns_error'" class="text-red-500">❌ DNS 解析失败，请检查域名是否正确</span>
                <span v-else-if="probeErrorType === 'connection_refused'" class="text-red-500">❌ 连接被拒绝，请确认服务是否在运行</span>
                <span v-else-if="probeErrorType === 'ssl_error'" class="text-amber-500">⚠️ SSL 证书错误，请检查 HTTPS 配置</span>
                <span v-else-if="probeErrorType === 'timeout'" class="text-amber-500">⏱️ 连接超时，服务响应过慢</span>
                <span v-else-if="probeErrorType === 'spec_not_found'" class="text-gray-600">🔍 未找到 OpenAPI 文档</span>
                <span v-else-if="probeErrorType === 'parse_error'" class="text-red-500">❌ 解析错误</span>
                <button
                  class="ml-auto px-3 py-1 text-xs text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
                  @click="handleProbe"
                >
                  重试
                </button>
              </div>
              <p v-else class="text-sm text-gray-600">未能自动发现 OpenAPI 文档，你可以：</p>
              <div class="flex flex-wrap gap-3">
                <label class="px-4 py-2 rounded-xl border border-dashed border-gray-300 text-sm text-gray-600 hover:border-indigo-400 hover:text-indigo-600 cursor-pointer transition-colors">
                  📁 上传 Spec 文件
                  <input
                    type="file"
                    accept=".json,.yaml,.yml"
                    class="hidden"
                    @change="handleFileUpload"
                  />
                </label>
                <RouterLink
                  to="/nodes/new"
                  class="px-4 py-2 rounded-xl border border-gray-300 text-sm text-gray-600 hover:border-indigo-400 hover:text-indigo-600 transition-colors"
                >
                  ✏️ 手动注册 Node
                </RouterLink>
              </div>
            </div>

            <!-- 上传区域（始终可用） -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">或者上传 Spec 文件</label>
              <div
                class="border-2 border-dashed rounded-xl p-6 text-center transition-colors"
                :class="dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'"
                @dragover.prevent="dragOver = true"
                @dragleave="dragOver = false"
                @drop.prevent="handleDrop"
              >
                <p class="text-sm text-gray-500">拖拽 .json / .yaml / .yml 文件到此处</p>
                <label class="mt-2 inline-block px-4 py-1.5 rounded-xl bg-gray-100 text-sm text-gray-600 hover:bg-gray-200 cursor-pointer transition-colors">
                  选择文件
                  <input
                    type="file"
                    accept=".json,.yaml,.yml"
                    class="hidden"
                    @change="handleFileUpload"
                  />
                </label>
              </div>
            </div>

            <!-- 错误消息 -->
            <div v-if="probeError" class="rounded-xl border border-red-200 bg-red-50 p-3">
              <p class="text-sm text-red-600">{{ probeError }}</p>
            </div>
          </div>
        </section>

        <!-- ② 接口预览 -->
        <section v-show="currentStep === 'preview'" class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0" style="background: linear-gradient(135deg, #7c3aed, #8b5cf6)">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">接口预览</h2>
              <p class="text-xs text-gray-400 mt-0.5">已发现 {{ probeDrafts.length }} 个接口，勾选要导入的</p>
            </div>
          </div>
          <div class="p-6 space-y-4">
            <!-- 全选/取消 -->
            <div class="flex items-center justify-between">
              <label class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  :indeterminate="someSelected && !allSelected"
                  class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  @change="toggleAll"
                />
                全选 ({{ selectedCount }}/{{ probeDrafts.length }})
              </label>
              <span class="text-xs text-gray-400">来自 {{ probeBaseUrl }}</span>
            </div>

            <!-- 接口列表 -->
            <div class="rounded-xl border border-gray-100 overflow-hidden">
              <table class="w-full text-sm">
                <thead class="bg-gray-50/80">
                  <tr>
                    <th class="w-10 px-3 py-2"></th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Method</th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Path</th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">名称</th>
                    <th class="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">描述</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr
                    v-for="(draft, i) in probeDrafts"
                    :key="i"
                    class="transition-colors"
                    :class="isImported(draft.endpoint)
                      ? 'bg-green-50 opacity-70'
                      : draft.selected ? 'hover:bg-gray-50' : 'opacity-50 hover:bg-gray-50'"
                  >
                    <td class="px-3 py-2 text-center">
                      <input
                        v-if="!isImported(draft.endpoint)"
                        v-model="draft.selected"
                        type="checkbox"
                        class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span v-else class="text-green-500 text-xs font-semibold">✓</span>
                    </td>
                    <td class="px-3 py-2">
                      <span
                        class="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                        :class="methodColor(draft.method)"
                      >{{ draft.method }}</span>
                    </td>
                    <td class="px-3 py-2 font-mono text-gray-600 max-w-[200px] truncate" :title="draft.endpoint">
                      {{ draft.endpoint }}
                      <span v-if="isImported(draft.endpoint)" class="ml-1.5 inline-block px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 text-[10px] font-medium">已导入</span>
                    </td>
                    <td class="px-3 py-2">
                      <input
                        v-model="draft.suggested_name"
                        :disabled="isImported(draft.endpoint)"
                        class="w-full border-0 bg-transparent text-sm text-gray-800 focus:outline-none focus:ring-1 focus:ring-indigo-400 rounded px-1 py-0.5 disabled:text-gray-400"
                      />
                    </td>
                    <td class="px-3 py-2 text-gray-500 max-w-[200px] truncate" :title="draft.description">
                      {{ draft.description || '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- ③ 导入配置 -->
        <section v-show="currentStep === 'import'" class="bg-white rounded-2xl border border-gray-100 overflow-hidden" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
          <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0" style="background: linear-gradient(135deg, #059669, #10b981)">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">导入配置</h2>
              <p class="text-xs text-gray-400 mt-0.5">设置公共属性并导入选中的接口</p>
            </div>
          </div>
          <div class="p-6 space-y-5">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <!-- Category -->
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">分类</label>
                <select
                  v-model="importConfig.category_id"
                  class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                >
                  <option value="">不设置</option>
                  <option v-for="c in categoryList" :key="c.id" :value="c.id">{{ c.display_name }}</option>
                </select>
              </div>
              <!-- Visibility -->
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">可见性</label>
                <select
                  v-model="importConfig.visibility"
                  class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                >
                  <option value="internal">内部</option>
                  <option value="public">公开</option>
                  <option value="private">私有</option>
                </select>
              </div>
            </div>
            <!-- Tags -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">标签（逗号分隔）</label>
              <input
                v-model="importConfig.tags"
                placeholder="api, external, auto-discovered"
                class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              />
            </div>
            <!-- Credential -->
            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">关联凭据（可选）</label>
              <select
                v-model="importConfig.credentialId"
                class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
              >
                <option value="">不关联凭据</option>
                <option v-for="c in credentials" :key="c.id" :value="c.id">{{ c.name }} ({{ c.auth_type }})</option>
              </select>
            </div>

            <!-- 导入汇总 -->
            <div class="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
              <p class="text-sm text-emerald-700">
                将导入 <strong>{{ selectedCount }}</strong> 个接口到命名空间
                <strong>{{ namespaceName }}</strong>
              </p>
            </div>

            <!-- 错误消息 -->
            <div v-if="importError" class="rounded-xl border border-red-200 bg-red-50 p-3">
              <p class="text-sm text-red-600">{{ importError }}</p>
            </div>

            <!-- 导入成功 -->
            <div v-if="importResult" class="rounded-xl border border-green-200 bg-green-50 p-4 space-y-2">
              <p class="text-sm text-green-700 font-medium">✓ 成功导入 {{ importResult.imported }} 个 Node</p>
              <div class="flex gap-3">
                <RouterLink
                  to="/nodes"
                  class="px-4 py-2 rounded-xl bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors"
                >
                  查看节点列表
                </RouterLink>
                <button
                  type="button"
                  class="px-4 py-2 rounded-xl border border-gray-300 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                  @click="resetAll"
                >
                  继续发现
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- 底部操作按钮 -->
        <div class="flex justify-between items-center pt-2">
          <button
            v-if="currentStep !== 'probe'"
            type="button"
            class="px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            @click="goBack"
          >
            上一步
          </button>
          <div v-else></div>
          <button
            v-if="currentStep === 'preview'"
            type="button"
            class="px-5 py-2.5 rounded-xl text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
            style="background: linear-gradient(135deg, #6366f1, #8b5cf6); box-shadow: 0 3px 10px rgba(99,102,241,0.25)"
            :disabled="selectedCount === 0"
            @click="goToImport"
          >
            下一步：导入配置
          </button>
          <button
            v-if="currentStep === 'import' && !importResult"
            type="button"
            class="px-5 py-2.5 rounded-xl text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
            style="background: linear-gradient(135deg, #059669, #10b981); box-shadow: 0 3px 10px rgba(16,185,129,0.25)"
            :disabled="importing || selectedCount === 0"
            @click="handleImport"
          >
            {{ importing ? '导入中..' : `导入 ${selectedCount} 个接口` }}
          </button>
        </div>

        <!-- 重复 URL 弹窗 -->
        <Teleport to="body">
          <div v-if="showDuplicateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showDuplicateModal = false">
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-100">
                <h3 class="text-sm font-semibold text-gray-900">⚠ 此地址已有发现记录</h3>
              </div>
              <div class="p-6 space-y-3">
                <p class="text-sm text-gray-600">该 URL 已有 <strong>{{ duplicateInfo?.existing_node_count ?? 0 }}</strong> 个已导入节点。</p>
                <p class="text-xs text-gray-400">你可以选择：</p>
              </div>
              <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
                <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900" @click="showDuplicateModal = false">取消</button>
                <button
                  class="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
                  @click="doProbe"
                >
                  继续探测（迭代更新）
                </button>
              </div>
            </div>
          </div>
        </Teleport>

        <!-- 认证配置弹窗 -->
        <Teleport to="body">
          <div v-if="showAuthModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showAuthModal = false">
            <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
              <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <h3 class="text-sm font-semibold text-gray-900">认证配置</h3>
                <button class="text-gray-400 hover:text-gray-600" @click="showAuthModal = false">✕</button>
              </div>
              <div class="p-6 space-y-4">
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">登录地址</label>
                  <input
                    v-model="authConfig.login_endpoint"
                    placeholder="https://api.example.com/auth/login"
                    class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                  />
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="flex flex-col gap-1.5">
                    <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">用户名字段</label>
                    <input
                      v-model="authConfig.username_key"
                      placeholder="username"
                      class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                    />
                  </div>
                  <div class="flex flex-col gap-1.5">
                    <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">用户名</label>
                    <input
                      v-model="authConfig.username"
                      class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                    />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="flex flex-col gap-1.5">
                    <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">密码字段</label>
                    <input
                      v-model="authConfig.password_key"
                      placeholder="password"
                      class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                    />
                  </div>
                  <div class="flex flex-col gap-1.5">
                    <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">密码</label>
                    <input
                      v-model="authConfig.password"
                      type="password"
                      class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                    />
                  </div>
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Token JSON 路径（可选）</label>
                  <input
                    v-model="authConfig.token_json_path"
                    placeholder="data.access_token"
                    class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 focus:bg-white transition-colors"
                  />
                  <p class="text-xs text-gray-400">留空将自动猜测</p>
                </div>
              </div>
              <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
                <button
                  type="button"
                  class="px-4 py-2 rounded-xl border border-gray-300 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                  @click="showAuthModal = false"
                >
                  取消
                </button>
                <button
                  type="button"
                  class="px-4 py-2 rounded-xl bg-amber-600 text-white text-sm font-medium hover:bg-amber-700 disabled:opacity-50 transition-colors"
                  :disabled="!authConfig.login_endpoint || !authConfig.username || !authConfig.password || probing"
                  @click="handleProbeWithAuth"
                >
                  {{ probing ? '探测中...' : '认证并探测' }}
                </button>
              </div>
            </div>
          </div>
        </Teleport>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { probeSpec, probeWithAuth, uploadSpec, batchImport, getImportedPaths, createSession, updateSession, checkDuplicate } from '@/api/discovery'
import { listCredentials } from '@/api/credentials'
import { listCategories } from '@/api/categories'
import type { Category } from '@/api/categories'
import type { NodeDraft, ProbeAttempt, BatchImportResponse } from '@/api/discovery'
import type { CredentialResponse } from '@/api/credentials'

const auth = useAuthStore()
const router = useRouter()

// --- Steps ---
const sections = reactive([
  { id: 'probe', label: '探测服务', done: false },
  { id: 'preview', label: '接口预览', done: false },
  { id: 'import', label: '导入配置', done: false },
])
const currentStep = ref<string>('probe')

// --- Probe ---
const baseUrl = ref('')
const probing = ref(false)
const probeAttempts = ref<ProbeAttempt[]>([])
const probeDrafts = ref<NodeDraft[]>([])
const probeBaseUrl = ref('')
const needsAuth = ref(false)
const probeFailed = ref(false)
const probeError = ref('')
const dragOver = ref(false)
const showAuthModal = ref(false)
const sessionId = ref<string | null>(null)

const authConfig = reactive({
  login_endpoint: '',
  username_key: 'username',
  username: '',
  password_key: 'password',
  password: '',
  token_json_path: '',
})

// --- Import ---
const importConfig = reactive({
  category_id: '',
  visibility: 'internal',
  tags: '',
  credentialId: '',
})
const importing = ref(false)
const importError = ref('')
const importResult = ref<BatchImportResponse | null>(null)
const credentials = ref<CredentialResponse[]>([])
const importedPaths = ref<Set<string>>(new Set())
const categoryList = ref<Category[]>([])
const probeErrorType = ref<string | null>(null)
const showDuplicateModal = ref(false)
const duplicateInfo = ref<{ existing_sessions: { id: string; base_url: string; status: string; created_at: string }[]; existing_node_count: number } | null>(null)

// --- Computed ---
const namespaceId = computed(() => auth.user?.namespaces?.[0]?.id ?? '')
const namespaceName = computed(() => auth.user?.namespaces?.[0]?.display_name || auth.user?.namespaces?.[0]?.slug || '默认')

const selectedCount = computed(() => probeDrafts.value.filter(d => d.selected && !importedPaths.value.has(d.endpoint)).length)
const allSelected = computed(() => probeDrafts.value.length > 0 && probeDrafts.value.every(d => importedPaths.value.has(d.endpoint) || d.selected))
const someSelected = computed(() => probeDrafts.value.some(d => !importedPaths.value.has(d.endpoint) && d.selected))

function isImported(endpoint: string) {
  return importedPaths.value.has(endpoint)
}

// Watch credentialId — load already-imported paths for diff highlight
watch(() => importConfig.credentialId, async (id) => {
  if (!id) {
    importedPaths.value = new Set()
    return
  }
  try {
    const res = await getImportedPaths(id)
    const data = res.data as any
    importedPaths.value = new Set(data.imported_paths ?? [])
    // Auto-deselect drafts that are already imported
    probeDrafts.value.forEach(d => {
      if (importedPaths.value.has(d.endpoint)) d.selected = false
    })
  } catch {
    importedPaths.value = new Set()
  }
})

// --- Methods ---
function methodColor(method: string) {
  const m = method.toUpperCase()
  if (m === 'GET') return 'bg-green-100 text-green-700'
  if (m === 'POST') return 'bg-blue-100 text-blue-700'
  if (m === 'PUT') return 'bg-amber-100 text-amber-700'
  if (m === 'PATCH') return 'bg-orange-100 text-orange-700'
  if (m === 'DELETE') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-700'
}

function toggleAll() {
  const newVal = !allSelected.value
  probeDrafts.value.forEach(d => d.selected = newVal)
}

function goBack() {
  if (currentStep.value === 'import') currentStep.value = 'preview'
  else if (currentStep.value === 'preview') currentStep.value = 'probe'
}

function goToImport() {
  sections[1].done = true
  currentStep.value = 'import'
  loadCredentials()
}

function setDrafts(drafts: NodeDraft[], url: string) {
  probeDrafts.value = drafts
  probeBaseUrl.value = url
  probeFailed.value = false
  needsAuth.value = false
  probeError.value = ''
  if (drafts.length) {
    sections[0].done = true
    currentStep.value = 'preview'
  }
}

async function handleProbe() {
  if (!baseUrl.value.trim()) return

  // 重复 URL 检测
  try {
    const dupRes = await checkDuplicate(baseUrl.value.trim())
    const dupData = dupRes.data as any
    if (dupData.is_duplicate) {
      duplicateInfo.value = { existing_sessions: dupData.existing_sessions, existing_node_count: dupData.existing_node_count }
      showDuplicateModal.value = true
      return
    }
  } catch {
    // 检测失败不阻止探测
  }

  await doProbe()
}

async function doProbe() {
  if (!baseUrl.value.trim()) return
  showDuplicateModal.value = false
  probing.value = true
  probeAttempts.value = []
  probeFailed.value = false
  needsAuth.value = false
  probeError.value = ''
  probeErrorType.value = null

  try {
    // 创建探测会话
    const sessionRes = await createSession({ base_url: baseUrl.value.trim(), source: 'probe' })
    sessionId.value = (sessionRes.data as any).id
  } catch {
    // 会话创建失败不阻止探测流程
  }

  try {
    const res = await probeSpec({ base_url: baseUrl.value.trim() })
    const data = res.data as any

    if (data.attempts) {
      probeAttempts.value = data.attempts
    }

    if (data.drafts) {
      setDrafts(data.drafts, data.base_url || baseUrl.value)
      if (sessionId.value) {
        await updateSession(sessionId.value, { status: 'found', spec_url: data.spec_url || undefined, total_operations: data.drafts.length }).catch(() => {})
      }
    } else if (data.needs_auth) {
      needsAuth.value = true
    } else if (data.found === false) {
      probeFailed.value = true
      probeErrorType.value = data.error_type || null
      if (sessionId.value) {
        await updateSession(sessionId.value, { status: 'failed' }).catch(() => {})
      }
    }
  } catch (e: any) {
    probeError.value = e.uiMessage || e.message || '探测失败'
    if (sessionId.value) {
      await updateSession(sessionId.value, { status: 'failed' }).catch(() => {})
    }
  } finally {
    probing.value = false
  }
}

async function handleProbeWithAuth() {
  probing.value = true
  probeError.value = ''

  const loginBody: Record<string, string> = {}
  loginBody[authConfig.username_key || 'username'] = authConfig.username
  loginBody[authConfig.password_key || 'password'] = authConfig.password

  try {
    const res = await probeWithAuth({
      base_url: baseUrl.value.trim(),
      login_endpoint: authConfig.login_endpoint,
      login_method: 'POST',
      login_body: loginBody,
      token_json_path: authConfig.token_json_path || undefined,
    })
    const data = res.data as any

    if (data.attempts) {
      probeAttempts.value = data.attempts
    }

    showAuthModal.value = false
    if (data.drafts) {
      setDrafts(data.drafts, data.base_url || baseUrl.value)
      if (sessionId.value) {
        await updateSession(sessionId.value, { status: 'found', total_operations: data.drafts.length }).catch(() => {})
      }
    } else {
      probeError.value = data.error || '认证探测未找到 OpenAPI 文档'
      if (sessionId.value) {
        await updateSession(sessionId.value, { status: 'failed' }).catch(() => {})
      }
    }
  } catch (e: any) {
    probeError.value = e.uiMessage || e.message || '认证探测失败'
  } finally {
    probing.value = false
  }
}

async function handleFileUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  await doUpload(file)
  input.value = ''
}

async function handleDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  await doUpload(file)
}

async function doUpload(file: File) {
  probing.value = true
  probeError.value = ''

  try {
    const sessionRes = await createSession({ base_url: file.name, source: 'upload' })
    sessionId.value = (sessionRes.data as any).id
  } catch {
    // 会话创建失败不阻止上传流程
  }

  try {
    const res = await uploadSpec(file)
    const data = res.data as any
    if (data.drafts) {
      setDrafts(data.drafts, data.base_url || baseUrl.value || file.name)
      if (sessionId.value) {
        await updateSession(sessionId.value, { status: 'found', total_operations: data.drafts.length }).catch(() => {})
      }
    } else {
      if (sessionId.value) {
        await updateSession(sessionId.value, { status: 'failed' }).catch(() => {})
      }
    }
  } catch (e: any) {
    probeError.value = e.uiMessage || e.message || '文件解析失败'
    if (sessionId.value) {
      await updateSession(sessionId.value, { status: 'failed' }).catch(() => {})
    }
  } finally {
    probing.value = false
  }
}

async function loadCredentials() {
  try {
    const res = await listCredentials()
    credentials.value = res.data as CredentialResponse[]
  } catch {
    // Non-critical
  }
}

async function handleImport() {
  if (!namespaceId.value) {
    importError.value = '未找到命名空间'
    return
  }
  importing.value = true
  importError.value = ''

  const selected = probeDrafts.value.filter(d => d.selected && !importedPaths.value.has(d.endpoint))
  const tags = importConfig.tags.split(',').map(t => t.trim()).filter(Boolean)

  try {
    const res = await batchImport({
      namespace_id: namespaceId.value,
      base_url: probeBaseUrl.value,
      credential_id: importConfig.credentialId || undefined,
      visibility: importConfig.visibility,
      session_id: sessionId.value ?? undefined,
      items: selected.map(d => ({
        name: d.suggested_name,
        display_name: d.display_name,
        description: d.description,
        endpoint: d.endpoint,
        method: d.method,
        input_schema: d.input_schema,
        output_schema: d.output_schema,
        category_id: importConfig.category_id || undefined,
        tags: tags.length ? tags : d.tags,
        source_path: d.endpoint,
      })),
    })
    importResult.value = res.data as BatchImportResponse
    sections[2].done = true
    router.push('/discover')
  } catch (e: any) {
    importError.value = e.uiMessage || e.message || '导入失败'
  } finally {
    importing.value = false
  }
}

function resetAll() {
  baseUrl.value = ''
  probeAttempts.value = []
  probeDrafts.value = []
  probeBaseUrl.value = ''
  needsAuth.value = false
  probeFailed.value = false
  probeError.value = ''
  importError.value = ''
  importResult.value = null
  importedPaths.value = new Set()
  importConfig.category_id = ''
  importConfig.visibility = 'internal'
  importConfig.tags = ''
  importConfig.credentialId = ''
  sessionId.value = null
  sections.forEach(s => s.done = false)
  currentStep.value = 'probe'
}

onMounted(() => {
  loadCredentials()
  listCategories().then(res => { categoryList.value = res.data }).catch(() => {})
})
</script>
