<template>
  <div>
    <!-- 加载骨架 -->
    <div v-if="loading" class="space-y-4">
      <div class="h-10 bg-gray-100 rounded-xl w-72 animate-pulse" />
      <div class="h-48 bg-gray-100 rounded-2xl animate-pulse" />
      <div class="h-48 bg-gray-100 rounded-2xl animate-pulse" />
    </div>

    <!-- 404 -->
    <div v-else-if="notFound" class="text-center py-24">
      <div class="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-gray-500 mb-4">节点不存在或已被删除</p>
      <RouterLink to="/nodes">
        <BaseButton variant="secondary">返回列表</BaseButton>
      </RouterLink>
    </div>

    <template v-else-if="node">
      <!-- 页头 -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ node.display_name || node.name }}</h1>
          <p class="text-sm font-mono text-gray-400 mt-0.5">{{ node.name }}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0 ml-4">
          <RouterLink :to="`/nodes/${node.id}/stats`">
            <button class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              统计
            </button>
          </RouterLink>
          <RouterLink :to="`/nodes/${node.id}/edit`">
            <button class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              编辑
            </button>
          </RouterLink>
          <button
            class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors rounded-xl border"
            :class="showExportPanel
              ? 'text-indigo-700 bg-indigo-50 border-indigo-200 hover:bg-indigo-100'
              : 'text-gray-600 bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'"
            @click="showExportPanel = !showExportPanel"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            导出
          </button>
          <RouterLink :to="`/nodes/${node.id}/invoke`">
            <BaseButton>调用此节点</BaseButton>
          </RouterLink>
          <button
            v-if="isOwner"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-xl hover:bg-red-50 hover:border-red-300 transition-colors"
            @click="confirmDeleteNode = true"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            删除
          </button>
        </div>
      </div>

      <!-- 元信息卡片 -->
      <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden mb-5">
        <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-indigo-50 to-white">
          <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h2 class="text-sm font-semibold text-gray-900">基本信息</h2>
            <p class="text-xs text-gray-500 mt-0.5">节点的身份标识与元数据</p>
          </div>
        </div>
        <div class="p-6 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-5">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">唯一标识</p>
            <p class="text-sm font-mono text-gray-700 bg-gray-50 px-2.5 py-1.5 rounded-lg inline-block">{{ node.name }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">显示名称</p>
            <p class="text-sm text-gray-700">{{ node.display_name || '—' }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">分类</p>
            <TypeBadge :category="node.category" />
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">状态</p>
            <StatusBadge :status="node.status" />
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">创建时间</p>
            <p class="text-sm text-gray-700">{{ formatDate(node.created_at) }}</p>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">所属部门</p>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-medium">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
              {{ node.department_slug || '—' }}
            </span>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">创建者</p>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
              {{ node.owner_username || '—' }}
            </span>
          </div>
          <div class="sm:col-span-2">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">描述</p>
            <p class="text-sm text-gray-600 leading-relaxed">{{ node.description || '暂无描述' }}</p>
          </div>
          <div v-if="node.tags?.length" class="sm:col-span-2">
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">标签</p>
            <div class="flex flex-wrap gap-1.5">
              <RouterLink
                v-for="tag in node.tags"
                :key="tag"
                :to="`/tags/${tag}`"
                class="px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
              >
                {{ tag }}
              </RouterLink>
            </div>
          </div>
        </div>
      </div>

      <!-- 凭据绑定信息 -->
      <div class="bg-white rounded-2xl border border-gray-100 overflow-hidden mb-5" style="box-shadow: 0 1px 3px rgba(0,0,0,0.04)">
        <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-indigo-50 to-white">
          <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
          </div>
          <div>
            <h2 class="text-sm font-semibold text-gray-900">服务凭据</h2>
            <p class="text-xs text-gray-500 mt-0.5">调用此 Node 时使用的鉴权凭据</p>
          </div>
        </div>
        <div class="px-6 py-4">
          <div v-if="node.credential_id" class="flex items-center gap-2">
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-medium">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
              已绑定凭据
            </span>
            <RouterLink to="/credentials" class="text-xs text-indigo-500 hover:text-indigo-700 transition-colors">管理凭据 →</RouterLink>
          </div>
          <div v-else class="flex items-center gap-2 text-sm text-gray-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            无（将按 base_url 前缀自动匹配凭据）
          </div>
        </div>
      </div>

      <!-- 来源信息（仅当节点由服务发现导入时显示） -->
      <div v-if="node.source_credential_id" class="bg-white rounded-2xl border border-sky-200 overflow-hidden mb-5">
        <div class="flex items-center gap-3 px-6 py-4 border-b border-sky-100 bg-gradient-to-r from-sky-50 to-white">
          <div class="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h2 class="text-sm font-semibold text-gray-900">来源服务</h2>
            <p class="text-xs text-gray-500 mt-0.5">此节点由服务发现自动导入</p>
          </div>
        </div>
        <div class="p-6 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-5">
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">服务名称</p>
            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-sky-50 text-sky-700 rounded-lg text-sm font-medium">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
              {{ node.source_service_name || '—' }}
            </span>
          </div>
          <div>
            <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">原始路径</p>
            <p class="text-sm font-mono text-gray-700 bg-gray-50 px-2.5 py-1.5 rounded-lg inline-block">{{ node.source_path || '—' }}</p>
          </div>
        </div>
      </div>

      <!-- 导出面板 -->
      <NodeExportPanel
        v-if="showExportPanel"
        :nodeId="node.id"
        :nodeName="node.name"
        :hasActiveVersion="hasActiveVersion"
        class="mb-5"
      />

      <!-- 版本列表 -->
      <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden mb-5">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-violet-50 to-white">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">版本列表</h2>
              <p class="text-xs text-gray-500 mt-0.5">管理节点的发布版本</p>
            </div>
          </div>
          <button
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-xl border transition-colors"
            :class="showVersionForm
              ? 'text-gray-600 bg-white border-gray-200 hover:bg-gray-50'
              : 'text-indigo-700 bg-indigo-50 border-indigo-200 hover:bg-indigo-100'"
            @click="showVersionForm = !showVersionForm; versionFormError = ''"
          >
            <svg v-if="!showVersionForm" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
            </svg>
            {{ showVersionForm ? '取消' : '新增版本' }}
          </button>
        </div>

        <!-- 新增版本表单 -->
        <div v-if="showVersionForm" class="px-6 py-5 border-b border-gray-100 bg-gray-50 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">版本号 <span class="text-red-500">*</span></label>
              <input
                v-model="versionForm.version"
                placeholder="1.0.0"
                class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
              />
            </div>
            <div class="flex items-end pb-2">
              <label class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                <input type="checkbox" v-model="versionForm.is_default" class="rounded accent-indigo-600" />
                设为默认版本
              </label>
            </div>
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">变更日志</label>
            <input
              v-model="versionForm.changelog"
              placeholder="本版本的主要变更内容..."
              class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
            />
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Runtime 配置 (JSON) <span class="text-red-500">*</span></label>
            <textarea
              v-model="versionForm.runtime_config_raw"
              rows="4"
              placeholder='{"type": "http", "endpoint": "https://...", "method": "POST"}'
              class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">输入 Schema (JSON)</label>
              <textarea
                v-model="versionForm.input_schema_raw"
                rows="4"
                placeholder='{"type": "object", "properties": {}}'
                class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
              />
            </div>
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">输出 Schema (JSON)</label>
              <textarea
                v-model="versionForm.output_schema_raw"
                rows="4"
                placeholder='{"type": "object", "properties": {}}'
                class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
              />
            </div>
          </div>
          <p v-if="versionFormError" class="text-red-500 text-xs flex items-center gap-1">
            <svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            {{ versionFormError }}
          </p>
          <div class="flex justify-end gap-2">
            <BaseButton variant="secondary" @click="showVersionForm = false; versionFormError = ''">取消</BaseButton>
            <BaseButton :disabled="submittingVersion" @click="handleCreateVersion">
              {{ submittingVersion ? '发布中...' : '发布版本' }}
            </BaseButton>
          </div>
        </div>

        <EmptyState v-if="versions.length === 0" description="暂无版本记录" />
        <template v-else>
          <!-- 操作错误提示 -->
          <div
            v-if="actionError"
            class="mx-6 my-3 flex items-start gap-2.5 bg-red-50 border border-red-200 rounded-xl px-4 py-3"
          >
            <svg class="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-700 flex-1">{{ actionError }}</p>
            <button class="text-red-400 hover:text-red-600" @click="actionError = ''">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">版本号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">变更日志</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">默认</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">创建时间</th>
              <th v-if="isOwner" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="v in versions" :key="v.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-6 py-3.5 font-mono text-sm text-gray-700">
                {{ v.version }}
                <span v-if="v.is_deprecated" class="ml-2 px-1.5 py-0.5 bg-red-50 text-red-500 border border-red-200 rounded text-xs">已废弃</span>
              </td>
              <td class="px-6 py-3.5 text-gray-500 text-xs max-w-xs truncate">{{ v.changelog || '—' }}</td>
              <td class="px-6 py-3.5">
                <span
                  v-if="v.is_default"
                  class="px-2.5 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-semibold"
                >
                  默认
                </span>
                <button
                  v-else
                  class="px-2.5 py-1 text-xs text-gray-500 border border-gray-200 rounded-full hover:border-indigo-300 hover:text-indigo-600 transition-colors disabled:opacity-40"
                  :disabled="settingDefault === v.version"
                  @click="handleSetDefault(v.version)"
                >
                  {{ settingDefault === v.version ? '设置中...' : '设为默认' }}
                </button>
              </td>
              <td class="px-6 py-3.5 text-gray-400 text-xs">{{ formatDate(v.created_at) }}</td>
              <td v-if="isOwner" class="px-6 py-3.5 text-right">
                <div class="inline-flex items-center gap-1">
                  <button
                    class="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                    title="编辑版本"
                    @click="startEditVersion(v)"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button
                    v-if="!v.is_default"
                    class="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="删除版本"
                    @click="deletingVersion = v.version"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        </template>
      </div>

      <!-- 编辑版本弹出面板 -->
      <div v-if="editingVersion" class="bg-white rounded-2xl border border-indigo-200 overflow-hidden shadow-lg shadow-indigo-100/30">
        <div class="flex items-center justify-between px-6 py-4 border-b border-indigo-100 bg-gradient-to-r from-indigo-50 to-white">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-gray-900">编辑版本 <span class="font-mono text-indigo-600">{{ editingVersion.version }}</span></h2>
              <p class="text-xs text-gray-500 mt-0.5">修改 schema、运行时配置和变更日志</p>
            </div>
          </div>
          <button class="text-gray-400 hover:text-gray-600 transition-colors" @click="cancelEdit">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="px-6 py-5 space-y-4">
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">变更日志</label>
            <input
              v-model="editForm.changelog"
              placeholder="本版本的主要变更内容..."
              class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
            />
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">Runtime 配置 (JSON)</label>
            <textarea
              v-model="editForm.runtime_config_raw"
              rows="4"
              class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">输入 Schema (JSON)</label>
              <textarea
                v-model="editForm.input_schema_raw"
                rows="4"
                class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
              />
            </div>
            <div>
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide block mb-1.5">输出 Schema (JSON)</label>
              <textarea
                v-model="editForm.output_schema_raw"
                rows="4"
                class="block w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
              />
            </div>
          </div>
          <p v-if="editFormError" class="text-red-500 text-xs flex items-center gap-1">
            <svg class="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>
            {{ editFormError }}
          </p>
          <div class="flex justify-end gap-2">
            <BaseButton variant="secondary" @click="cancelEdit">取消</BaseButton>
            <BaseButton :disabled="savingEdit" @click="handleSaveEdit">
              {{ savingEdit ? '保存中...' : '保存修改' }}
            </BaseButton>
          </div>
        </div>
      </div>

      <!-- 调用日志 -->
      <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-emerald-50 to-white">
          <div class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shrink-0">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <h2 class="text-sm font-semibold text-gray-900">最近调用日志</h2>
            <p class="text-xs text-gray-500 mt-0.5">最近 10 条调用记录</p>
          </div>
        </div>
        <EmptyState v-if="logs.length === 0" description="暂无调用记录" />
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 border-b border-gray-100">
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">调用时间</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">耗时 (ms)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-6 py-3.5 text-gray-500 text-xs">{{ formatDate(log.created_at) }}</td>
              <td class="px-6 py-3.5">
                <span
                  :class="[
                    'px-2.5 py-1 rounded-full text-xs font-medium',
                    log.status === 'success'
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : log.status === 'timeout'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-red-50 text-red-700 border border-red-200',
                  ]"
                >
                  {{ log.status }}
                </span>
              </td>
              <td class="px-6 py-3.5 text-gray-500 text-xs tabular-nums">{{ log.latency_ms ?? '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- 删除节点确认弹窗 -->
    <div
      v-if="confirmDeleteNode"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="confirmDeleteNode = false"
    >
      <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div>
            <h3 class="text-base font-semibold text-gray-900">删除节点</h3>
            <p class="text-sm text-gray-500 mt-0.5">此操作不可撤销</p>
          </div>
        </div>
        <p class="text-sm text-gray-600 mb-6">
          确定要删除节点 <span class="font-semibold text-gray-900">{{ node?.display_name || node?.name }}</span> 吗？删除后该节点的所有版本和调用日志将一并移除。
        </p>
        <div class="flex justify-end gap-3">
          <BaseButton variant="secondary" :disabled="deletingNodeLoading" @click="confirmDeleteNode = false">取消</BaseButton>
          <button
            class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-xl transition-colors disabled:opacity-50"
            :disabled="deletingNodeLoading"
            @click="handleDeleteNode"
          >
            {{ deletingNodeLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除版本确认弹窗 -->
    <div
      v-if="deletingVersion"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="deletingVersion = null"
    >
      <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div>
            <h3 class="text-base font-semibold text-gray-900">删除版本</h3>
            <p class="text-sm text-gray-500 mt-0.5">此操作不可撤销</p>
          </div>
        </div>
        <p class="text-sm text-gray-600 mb-6">
          确定要删除版本 <span class="font-mono font-semibold text-gray-900">{{ deletingVersion }}</span> 吗？
        </p>
        <div class="flex justify-end gap-3">
          <BaseButton variant="secondary" :disabled="deletingVersionLoading" @click="deletingVersion = null">取消</BaseButton>
          <button
            class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-xl transition-colors disabled:opacity-50"
            :disabled="deletingVersionLoading"
            @click="handleDeleteVersion(deletingVersion!)"
          >
            {{ deletingVersionLoading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getNode, listVersions, getLogs, createVersion, updateVersion, setDefaultVersion, deleteNode, deleteVersion } from '@/api/nodes'
import type { NodeItem, NodeVersion, InvocationLog } from '@/api/nodes'
import BaseButton from '@/components/BaseButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TypeBadge from '@/components/TypeBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import NodeExportPanel from '@/components/NodeExportPanel.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const id = route.params.id as string

const node = ref<NodeItem | null>(null)
const versions = ref<NodeVersion[]>([])
const logs = ref<InvocationLog[]>([])
const loading = ref(true)
const notFound = ref(false)
const showExportPanel = ref(false)

// 版本管理状态
const showVersionForm = ref(false)
const submittingVersion = ref(false)
const versionFormError = ref('')
const settingDefault = ref<string | null>(null)
const actionError = ref('')
const isOwner = computed(() => {
  if (!node.value || !authStore.user) return false
  // 用户所属部门列表中包含节点的部门即有写权限
  return authStore.user.departments?.some(ns => ns.id === node.value!.department_id) ?? false
})
const confirmDeleteNode = ref(false)
const deletingNodeLoading = ref(false)
const deletingVersion = ref<string | null>(null)
const deletingVersionLoading = ref(false)
const editingVersion = ref<NodeVersion | null>(null)
const editForm = reactive({
  changelog: '',
  runtime_config_raw: '',
  input_schema_raw: '',
  output_schema_raw: '',
})
const editFormError = ref('')
const savingEdit = ref(false)
const versionForm = reactive({
  version: '',
  changelog: '',
  is_default: false,
  runtime_config_raw: '',
  input_schema_raw: '{"type": "object", "properties": {}}',
  output_schema_raw: '{"type": "object", "properties": {}}',
})

const hasActiveVersion = computed(() =>
  versions.value.some(v => v.is_default)
)

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

async function handleCreateVersion() {
  versionFormError.value = ''
  if (!versionForm.version.trim()) {
    versionFormError.value = '版本号不能为空'
    return
  }
  let runtime_config: Record<string, unknown>
  let input_schema: Record<string, unknown>
  let output_schema: Record<string, unknown>
  try {
    runtime_config = JSON.parse(versionForm.runtime_config_raw || '{}')
  } catch {
    versionFormError.value = 'Runtime 配置不是合法的 JSON'
    return
  }
  try {
    input_schema = JSON.parse(versionForm.input_schema_raw || '{}')
  } catch {
    versionFormError.value = '输入 Schema 不是合法的 JSON'
    return
  }
  try {
    output_schema = JSON.parse(versionForm.output_schema_raw || '{}')
  } catch {
    versionFormError.value = '输出 Schema 不是合法的 JSON'
    return
  }
  submittingVersion.value = true
  try {
    await createVersion(id, {
      version: versionForm.version.trim(),
      changelog: versionForm.changelog || undefined,
      is_default: versionForm.is_default,
      runtime_config,
      input_schema,
      output_schema,
    })
    const res = await listVersions(id)
    versions.value = res.data
    showVersionForm.value = false
    versionForm.version = ''
    versionForm.changelog = ''
    versionForm.is_default = false
  } catch (e: unknown) {
    versionFormError.value = (e as { uiMessage?: string }).uiMessage || '发布失败，请检查填写内容'
  } finally {
    submittingVersion.value = false
  }
}

function startEditVersion(v: NodeVersion) {
  editingVersion.value = v
  editForm.changelog = v.changelog || ''
  editForm.runtime_config_raw = JSON.stringify(v.runtime_config, null, 2)
  editForm.input_schema_raw = JSON.stringify(v.input_schema, null, 2)
  editForm.output_schema_raw = JSON.stringify(v.output_schema, null, 2)
  editFormError.value = ''
}

function cancelEdit() {
  editingVersion.value = null
  editFormError.value = ''
}

async function handleSaveEdit() {
  if (!editingVersion.value) return
  editFormError.value = ''
  let runtime_config: Record<string, unknown> | undefined
  let input_schema: Record<string, unknown> | undefined
  let output_schema: Record<string, unknown> | undefined
  try {
    runtime_config = JSON.parse(editForm.runtime_config_raw || '{}')
  } catch {
    editFormError.value = 'Runtime 配置不是合法的 JSON'
    return
  }
  try {
    input_schema = JSON.parse(editForm.input_schema_raw || '{}')
  } catch {
    editFormError.value = '输入 Schema 不是合法的 JSON'
    return
  }
  try {
    output_schema = JSON.parse(editForm.output_schema_raw || '{}')
  } catch {
    editFormError.value = '输出 Schema 不是合法的 JSON'
    return
  }
  savingEdit.value = true
  try {
    await updateVersion(id, editingVersion.value.version, {
      changelog: editForm.changelog || undefined,
      runtime_config,
      input_schema,
      output_schema,
    })
    const res = await listVersions(id)
    versions.value = res.data
    editingVersion.value = null
  } catch (e: unknown) {
    editFormError.value = (e as { uiMessage?: string }).uiMessage || '保存失败，请稍后重试'
  } finally {
    savingEdit.value = false
  }
}

async function handleSetDefault(version: string) {
  actionError.value = ''
  settingDefault.value = version
  try {
    await setDefaultVersion(id, version)
    const res = await listVersions(id)
    versions.value = res.data
  } catch (e: unknown) {
    actionError.value = (e as { uiMessage?: string }).uiMessage || '操作失败，请稍后重试'
  } finally {
    settingDefault.value = null
  }
}

async function handleDeleteNode() {
  deletingNodeLoading.value = true
  try {
    await deleteNode(id)
    router.push('/nodes')
  } catch (e: unknown) {
    actionError.value = (e as { uiMessage?: string }).uiMessage || '删除节点失败'
    confirmDeleteNode.value = false
  } finally {
    deletingNodeLoading.value = false
  }
}

async function handleDeleteVersion(version: string) {
  deletingVersionLoading.value = true
  try {
    await deleteVersion(id, version)
    const res = await listVersions(id)
    versions.value = res.data
    deletingVersion.value = null
  } catch (e: unknown) {
    actionError.value = (e as { uiMessage?: string }).uiMessage || '删除版本失败'
    deletingVersion.value = null
  } finally {
    deletingVersionLoading.value = false
  }
}

onMounted(async () => {
  try {
    const nodeRes = await getNode(id)
    node.value = nodeRes.data
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 404) {
      notFound.value = true
    }
    loading.value = false
    return
  }

  // 版本和日志独立加载，失败不影响页面展示
  try {
    const versionsRes = await listVersions(id)
    versions.value = versionsRes.data
    if (versionsRes.data.length > 0) {
      const latest = versionsRes.data[versionsRes.data.length - 1]
      versionForm.runtime_config_raw = JSON.stringify(latest.runtime_config, null, 2)
      versionForm.input_schema_raw = JSON.stringify(latest.input_schema, null, 2)
      versionForm.output_schema_raw = JSON.stringify(latest.output_schema, null, 2)
    }
  } catch { /* ignore */ }

  try {
    const logsRes = await getLogs(id, { page_size: 10 })
    logs.value = logsRes.data
  } catch { /* ignore */ }

  loading.value = false
})
</script>
