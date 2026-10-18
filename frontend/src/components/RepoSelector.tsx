import React, { useState } from 'react';
import {
  FolderGit2,
  GitBranch,
  Upload,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileArchive,
} from 'lucide-react';
import { Repository } from '../types';
import { registerRepository, uploadRepository, indexRepository } from '../api';

interface RepoSelectorProps {
  repositories: Repository[];
  currentRepo: Repository | null;
  onSelectRepo: (repo: Repository) => void;
  onRepoIndexed: (repo: Repository) => void;
  indexing: boolean;
  setIndexing: (val: boolean) => void;
}

export const RepoSelector: React.FC<RepoSelectorProps> = ({
  repositories,
  currentRepo,
  onSelectRepo,
  onRepoIndexed,
  indexing,
  setIndexing,
}) => {
  const [sourceMode, setSourceMode] = useState<'sample' | 'github' | 'upload'>('sample');
  const [githubUrl, setGithubUrl] = useState('');
  const [repoName, setRepoName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRegisterSample = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await registerRepository('sample');
      const repoObj: Repository = {
        repo_id: res.repo_id,
        name: res.name,
        path: res.path,
        is_sample: true,
        status: 'registered',
      };
      onSelectRepo(repoObj);
      await triggerIndex(repoObj);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterGithub = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await registerRepository('github', githubUrl, undefined, repoName);
      const repoObj: Repository = {
        repo_id: res.repo_id,
        name: res.name,
        path: res.path,
        is_sample: false,
        status: 'registered',
      };
      onSelectRepo(repoObj);
      await triggerIndex(repoObj);
      setGithubUrl('');
      setRepoName('');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadZip = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await uploadRepository(selectedFile, repoName);
      const repoObj: Repository = {
        repo_id: res.repo_id,
        name: res.name,
        path: res.path,
        is_sample: false,
        status: 'registered',
      };
      onSelectRepo(repoObj);
      await triggerIndex(repoObj);
      setSelectedFile(null);
      setRepoName('');
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const triggerIndex = async (repo: Repository) => {
    try {
      setIndexing(true);
      const indexRes = await indexRepository(repo.repo_id);
      const updatedRepo: Repository = {
        ...repo,
        status: 'indexed',
        total_files: indexRes.total_files,
        total_symbols: indexRes.total_symbols,
        total_tests: indexRes.total_tests,
        total_relationships: indexRes.total_relationships,
      };
      onRepoIndexed(updatedRepo);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIndexing(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 mb-4 gap-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-brand-400" />
            Repository Source & Ingestion
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingest Python source repositories to build the FalkorDB dependency graph
          </p>
        </div>

        {/* Ingestion Mode Selector */}
        <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setSourceMode('sample')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              sourceMode === 'sample' ? 'bg-brand-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Sample Repo
          </button>
          <button
            onClick={() => setSourceMode('github')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              sourceMode === 'github' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            GitHub URL
          </button>
          <button
            onClick={() => setSourceMode('upload')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1.5 ${
              sourceMode === 'upload' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            Upload ZIP
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Mode Form Content */}
      <div className="mb-4">
        {sourceMode === 'sample' && (
          <div className="flex flex-col sm:flex-row items-center justify-between p-4 rounded-xl bg-gradient-to-r from-brand-950/40 to-slate-950 border border-brand-500/20 gap-4">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-brand-400" />
                Sample Auth & Payments Service
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                A multi-layer Python application (`models`, `db`, `auth`, `services`, `controllers`, `tests`) designed for testing complex multi-hop impact scenarios like modifying `authenticate_user()`.
              </p>
            </div>
            <button
              onClick={handleRegisterSample}
              disabled={loading || indexing}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md flex items-center gap-2 disabled:opacity-50 whitespace-nowrap"
            >
              {loading || indexing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Indexing in FalkorDB...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  Load & Index Sample
                </>
              )}
            </button>
          </div>
        )}

        {sourceMode === 'github' && (
          <form onSubmit={handleRegisterGithub} className="flex flex-col sm:flex-row gap-3">
            <input
              type="url"
              placeholder="https://github.com/owner/repository"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              required
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={loading || indexing || !githubUrl}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <GitBranch className="w-3.5 h-3.5" />
                  Clone & Ingest
                </>
              )}
            </button>
          </form>
        )}

        {sourceMode === 'upload' && (
          <form onSubmit={handleUploadZip} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 border border-dashed border-slate-700 rounded-xl px-4 py-2 bg-slate-950 flex items-center justify-between">
              <label className="text-xs text-slate-400 cursor-pointer flex items-center gap-2">
                <FileArchive className="w-4 h-4 text-blue-400" />
                {selectedFile ? selectedFile.name : 'Choose a Python repository ZIP archive...'}
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
              </label>
              {selectedFile && (
                <span className="text-[10px] text-slate-500">
                  ({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)
                </span>
              )}
            </div>
            <button
              type="submit"
              disabled={loading || indexing || !selectedFile}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Extracting...
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  Upload & Index
                </>
              )}
            </button>
          </form>
        )}
      </div>

      {/* Available Repositories Pill List */}
      {repositories.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap pt-2">
          <span className="text-xs text-slate-400 font-medium">Active Repositories:</span>
          {repositories.map((repo) => {
            const isSelected = currentRepo?.repo_id === repo.repo_id;
            return (
              <div
                key={repo.repo_id}
                onClick={() => onSelectRepo(repo)}
                className={`cursor-pointer px-3 py-1 rounded-lg text-xs font-medium border flex items-center gap-2 transition-all ${
                  isSelected
                    ? 'bg-slate-800 border-brand-500/50 text-white shadow-sm'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>{repo.name}</span>
                {repo.status === 'indexed' ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400"></span>
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                )}
                {isSelected && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      triggerIndex(repo);
                    }}
                    title="Re-index into FalkorDB"
                    className="p-1 hover:text-brand-300"
                  >
                    <RefreshCw className={`w-3 h-3 ${indexing ? 'animate-spin' : ''}`} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
