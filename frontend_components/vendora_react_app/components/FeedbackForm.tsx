import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useToast } from "@/hooks/use-toast";

interface FeedbackFormProps {
  taskId: string; // The ID of the task/insight to provide feedback for
  onSubmitSuccess?: () => void; // Optional callback for when feedback is submitted successfully
}

interface FeedbackPayload {
  rating: number; // e.g., 1-5
  comment?: string;
  // Add any other fields your backend expects for feedback
}

export function FeedbackForm({ taskId, onSubmitSuccess }: FeedbackFormProps) {
  const [rating, setRating] = useState<number | undefined>(undefined);
  const [comment, setComment] = useState('');
  const { toast } = useToast();

  const submitFeedbackMutation = useMutation(
    (feedbackData: FeedbackPayload) => api.submitFeedback(taskId, feedbackData),
    {
      onSuccess: () => {
        toast({ title: "Feedback Submitted", description: "Thank you for your feedback!" });
        setRating(undefined);
        setComment('');
        if (onSubmitSuccess) {
          onSubmitSuccess();
        }
      },
      onError: (error: Error) => {
        toast({ title: "Feedback Error", description: error.message || "Could not submit feedback.", variant: "destructive" });
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === undefined) {
      toast({ title: "Feedback Error", description: "Please select a rating.", variant: "destructive" });
      return;
    }
    submitFeedbackMutation.mutate({ rating, comment });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 border rounded-lg bg-slate-50">
      <Label className="text-lg font-semibold">Provide Feedback</Label>

      <div>
        <Label htmlFor={`rating-${taskId}`}>Rating (1 = Poor, 5 = Excellent)</Label>
        <RadioGroup
          defaultValue={rating?.toString()}
          onValueChange={(value) => setRating(parseInt(value))}
          className="flex space-x-2 mt-1"
          id={`rating-${taskId}`}
        >
          {[1, 2, 3, 4, 5].map((value) => (
            <div key={value} className="flex items-center space-x-1">
              <RadioGroupItem value={value.toString()} id={`r${value}-${taskId}`} />
              <Label htmlFor={`r${value}-${taskId}`}>{value}</Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      <div>
        <Label htmlFor={`comment-${taskId}`}>Comments (Optional)</Label>
        <Textarea
          id={`comment-${taskId}`}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Tell us more about your experience..."
          rows={3}
        />
      </div>
      <Button type="submit" disabled={submitFeedbackMutation.isLoading}>
        {submitFeedbackMutation.isLoading ? 'Submitting...' : 'Submit Feedback'}
      </Button>
    </form>
  );
}
