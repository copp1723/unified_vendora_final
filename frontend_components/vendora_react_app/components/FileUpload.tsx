import React, { useRef, useState } from 'react';
import { Upload, X, FileText, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';

interface FileUploadProps {
  onUpload: (files: File[]) => Promise<void>;
  acceptedFormats?: string[];
  maxFiles?: number;
  maxSizeMB?: number;
}

interface UploadedFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onUpload,
  acceptedFormats = ['.csv', '.xlsx', '.xls'],
  maxFiles = 10,
  maxSizeMB = 50
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const validateFiles = (files: FileList | File[]): File[] => {
    const fileArray = Array.from(files);
    const validFiles: File[] = [];

    for (const file of fileArray) {
      // Check file size
      const sizeInMB = file.size / (1024 * 1024);
      if (sizeInMB > maxSizeMB) {
        toast({
          title: "File too large",
          description: `${file.name} exceeds ${maxSizeMB}MB limit`,
          variant: "destructive"
        });
        continue;
      }

      // Check file type
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedFormats.includes(extension)) {
        toast({
          title: "Invalid file type",
          description: `${file.name} is not a supported format`,
          variant: "destructive"
        });
        continue;
      }

      validFiles.push(file);
    }

    // Check max files limit
    if (validFiles.length + uploadedFiles.length > maxFiles) {
      toast({
        title: "Too many files",
        description: `Maximum ${maxFiles} files allowed`,
        variant: "destructive"
      });
      return validFiles.slice(0, maxFiles - uploadedFiles.length);
    }

    return validFiles;
  };

  const handleFiles = async (files: FileList | File[]) => {
    const validFiles = validateFiles(files);
    if (validFiles.length === 0) return;

    // Add files to state
    const newFiles: UploadedFile[] = validFiles.map(file => ({
      file,
      progress: 0,
      status: 'pending' as const
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);
    setIsUploading(true);

    try {
      // Update status to uploading
      setUploadedFiles(prev => 
        prev.map(f => 
          newFiles.find(nf => nf.file === f.file) 
            ? { ...f, status: 'uploading' as const } 
            : f
        )
      );

      // Simulate progress (replace with actual upload progress)
      const interval = setInterval(() => {
        setUploadedFiles(prev => 
          prev.map(f => {
            if (f.status === 'uploading' && f.progress < 90) {
              return { ...f, progress: f.progress + 10 };
            }
            return f;
          })
        );
      }, 200);

      await onUpload(validFiles);

      clearInterval(interval);

      // Update status to success
      setUploadedFiles(prev => 
        prev.map(f => 
          newFiles.find(nf => nf.file === f.file) 
            ? { ...f, status: 'success' as const, progress: 100 } 
            : f
        )
      );

      toast({
        title: "Upload successful",
        description: `${validFiles.length} file(s) uploaded successfully`
      });
    } catch (error: any) {
      // Update status to error
      setUploadedFiles(prev => 
        prev.map(f => 
          newFiles.find(nf => nf.file === f.file) 
            ? { ...f, status: 'error' as const, error: error.message } 
            : f
        )
      );

      toast({
        title: "Upload failed",
        description: error.message || "An error occurred during upload",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (isUploading) return;
    
    const files = e.dataTransfer.files;
    handleFiles(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors duration-200
          ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedFormats.join(',')}
          onChange={handleFileInput}
          className="hidden"
          disabled={isUploading}
        />
        <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600 mb-2">
          {isDragOver
            ? "Drop the files here..."
            : "Drag and drop your files here, or click to browse"}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Supported formats: {acceptedFormats.join(', ')} (max {maxSizeMB}MB per file)
        </p>
        <Button variant="outline" disabled={isUploading} type="button">
          Select Files
        </Button>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium">Uploaded Files</h4>
          {uploadedFiles.map((uploadedFile, index) => (
            <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
              <FileText className="h-5 w-5 text-gray-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{uploadedFile.file.name}</p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(uploadedFile.file.size)}
                </p>
                {uploadedFile.status === 'uploading' && (
                  <Progress value={uploadedFile.progress} className="h-1 mt-2" />
                )}
                {uploadedFile.status === 'error' && (
                  <p className="text-xs text-red-600 mt-1">{uploadedFile.error}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {uploadedFile.status === 'pending' && (
                  <span className="text-xs text-gray-500">Pending</span>
                )}
                {uploadedFile.status === 'uploading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                )}
                {uploadedFile.status === 'success' && (
                  <span className="text-xs text-green-600">✓ Uploaded</span>
                )}
                {uploadedFile.status === 'error' && (
                  <span className="text-xs text-red-600">✗ Failed</span>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  disabled={uploadedFile.status === 'uploading'}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
