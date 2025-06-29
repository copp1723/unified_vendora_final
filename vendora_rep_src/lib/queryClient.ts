import { QueryClient, QueryFunction, MutationFunction } from "@tanstack/react-query";
import { api } from './api'; // Import the new api client

// Helper function to adapt api client methods to be used as queryFn or mutationFn
// For GET requests (queries)
const adaptApiQuery = <T>(apiMethod: (...args: any[]) => Promise<T>): QueryFunction<T> => {
  return async ({ queryKey }) => {
    // queryKey is an array, first element is usually the path or a unique key,
    // subsequent elements can be parameters.
    // We need to decide how to pass parameters from queryKey to apiMethod.
    // For simplicity, let's assume the apiMethod doesn't need params from queryKey for now,
    // or that params are handled differently (e.g. closures or by creating specific query functions).
    // If params are needed, the structure of queryKey and how it maps to apiMethod params must be defined.
    // Example: const [_, params] = queryKey; return apiMethod(params);

    // This is a generic wrapper. Specific query functions might be needed if params are complex.
    // For now, let's assume apiMethod is called without arguments from queryKey here.
    // Or, if queryKey[0] is a path, and api.makeRequest is made public, it could be used.
    // However, using dedicated methods from `api` is cleaner.

    // This generic approach might be too simplistic if methods require different arguments.
    // A more robust way would be to create specific query functions for each API call.
    // For example:
    // queryFn: () => api.getTaskStatus(taskId)
    // In this generic wrapper, we'll assume the method is parameter-less or params are bound
    // For example, in useQuery: useQuery(['taskStatus', taskId], () => api.getTaskStatus(taskId))
    // So the queryFn passed to defaultOptions doesn't directly call apiMethod with queryKey params.
    // Instead, the actual query function is provided at the useQuery call site.

    // The default queryFn in QueryClient is a fallback.
    // It's often better to provide queryFn directly in useQuery for type safety and clarity.
    // For this template, we'll make a simple default that might not be universally applicable.
    // It assumes queryKey[0] is a string that doesn't directly map to an API method without params.
    console.warn("Default queryFn is being used. Consider providing a specific queryFn for:", queryKey);
    // This default function will likely not work correctly for most actual queries
    // as it doesn't know which api method to call with which parameters.
    // It's better to define queryFn at the useQuery call.
    // For example, `useQuery(['task', taskId], () => api.getTaskStatus(taskId))`
    // The `api` methods themselves handle the actual fetching.
    throw new Error(`Default queryFn called for ${queryKey.join('/')}. Please provide a specific queryFn.`);
  };
};

// For POST/PUT/DELETE requests (mutations)
// This is a generic wrapper. Specific mutation functions are usually better.
const adaptApiMutation = <T, V>(apiMethod: (variables: V) => Promise<T>): MutationFunction<T, V> => {
  return async (variables: V) => {
    return apiMethod(variables);
  };
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // It's generally recommended to provide the queryFn per query,
      // especially if they need parameters.
      // queryFn: adaptApiQuery(someDefaultApiMethod), // Replace with a sensible default or remove
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity, // Cache data indefinitely, refetch manually or with invalidation
      retry: (failureCount, error: any) => {
        // Do not retry on 4xx client errors
        if (error.message && (error.message.includes('401') || error.message.includes('403') || error.message.includes('404'))) {
          return false;
        }
        return failureCount < 3; // Retry up to 3 times for other errors
      },
    },
    mutations: {
      // mutationFn: adaptApiMutation(someDefaultApiMutation), // Replace or remove
      retry: (failureCount, error: any) => {
        if (error.message && (error.message.includes('401') || error.message.includes('403'))) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});

// Example of how you might create specific hooks or functions for react-query:
// export const useTaskStatus = (taskId: string) => {
//   return useQuery(['taskStatus', taskId], () => api.getTaskStatus(taskId), {
//     enabled: !!taskId, // Only run if taskId is available
//   });
// };

// export const useSubmitQuery = () => {
//   return useMutation((query: string) => api.submitQuery(query));
// };

// The apiRequest function is no longer needed here as api.ts handles requests.
// The getQueryFn is also not directly applicable in the same way.
// Error handling (like throwIfResNotOk) is now within api.makeRequest.
// Unauthorized behavior (on401) should be handled by global error handlers in react-query
// or by checking error status in individual query/mutation error callbacks.
// Firebase token refresh logic would typically be part of getAuthToken in api.ts.
