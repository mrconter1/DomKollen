import { DocumentTextIcon, CalendarIcon } from '@heroicons/react/24/outline';
import { CourtCase } from '@/types/CourtCase';

// Tag color mapping
const TAG_COLORS: { [key: string]: string } = {
  // Violent crimes (red)
  'våldtäkt': 'red',
  'mord': 'red',
  'kroppsskada': 'red',
  
  // Serious modifiers and violence-related (orange)
  'grov': 'orange',
  'våld': 'orange',
  'vapen': 'orange',
  'tvång': 'orange',
  
  // Crimes against children and sexual offenses (purple)
  'barn': 'purple',
  'sexuellt': 'purple',
  
  // Personal integrity crimes (pink)
  'kränkande': 'pink',
  'förtal': 'pink',
  
  // Negligence and misconduct (yellow)
  'vållande': 'yellow',
  'tjänstefel': 'yellow',
  
  // Drug and financial crimes (green)
  'narkotika': 'green',
  'bokföring': 'green',
  
  // Default for any uncategorized tags
  'default': 'blue'
};

interface Props {
  courtCase: CourtCase;
}

export const CourtCaseCard: React.FC<Props> = ({ courtCase }) => {
  const getTagColor = (tag: string) => {
    return TAG_COLORS[tag] || TAG_COLORS.default;
  };

  const getVisibleTags = () => {
    if (!courtCase.tags || !courtCase.keyword_counts) return [];

    // Calculate total mentions
    const totalMentions = Object.values(courtCase.keyword_counts).reduce((a, b) => a + b, 0);
    
    // Get the maximum count for any tag
    const maxCount = Math.max(...Object.values(courtCase.keyword_counts));

    // Filter tags based on both relative and absolute thresholds
    return courtCase.tags.filter(tag => {
      const count = courtCase.keyword_counts[tag];
      
      // Relative threshold: Tag must represent at least 5% of total mentions
      const relativeThreshold = count / totalMentions >= 0.05;
      
      // Absolute threshold: Tag must appear at least 3 times OR
      // be at least 20% of the maximum count for any tag
      const absoluteThreshold = count >= 3 || count / maxCount >= 0.2;
      
      return relativeThreshold && absoluteThreshold;
    });
  };

  const visibleTags = getVisibleTags();

  return (
    <div className="group relative bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 border border-gray-700/50">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      <div className="relative flex flex-col h-full">
        <div className="flex-grow space-y-4">
          <div className="flex flex-col space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                Cases
              </span>
              {courtCase.date && (
                <div className="flex items-center text-gray-400 text-sm">
                  <CalendarIcon className="h-4 w-4 mr-1" />
                  {courtCase.date}
                </div>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {courtCase.court_ids.map((id) => (
                <div
                  key={id}
                  className="flex items-center text-lg font-bold text-white bg-gray-800/50 rounded px-2 py-0.5"
                >
                  {id}
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400">
              Area
            </span>
            <p className="text-gray-400">
              {courtCase.area}
            </p>
          </div>

          {visibleTags.length > 0 ? (
            <div className="space-y-2">
              <span className="text-sm text-gray-500">Primary Tags:</span>
              <div className="flex flex-wrap gap-2">
                {visibleTags.map((tag) => {
                  const color = getTagColor(tag);
                  const count = courtCase.keyword_counts[tag];
                  return (
                    <span
                      key={tag}
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                        ${color === 'red' ? 'bg-red-500/10 text-red-400' : 
                          color === 'orange' ? 'bg-orange-500/10 text-orange-400' :
                          color === 'purple' ? 'bg-purple-500/10 text-purple-400' :
                          color === 'pink' ? 'bg-pink-500/10 text-pink-400' :
                          color === 'yellow' ? 'bg-yellow-500/10 text-yellow-400' :
                          color === 'green' ? 'bg-emerald-500/10 text-emerald-400' :
                          'bg-blue-500/10 text-blue-400'}`}
                    >
                      {tag}
                      {count && (
                        <span className="ml-1 px-1.5 py-0.5 rounded-full bg-gray-700/50 text-gray-400 text-xs">
                          {count}
                        </span>
                      )}
                    </span>
                  );
                })}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No significant tags found</p>
          )}
        </div>
        
        <div className="mt-4 pt-4 border-t border-gray-700/50">
          <a
            href={courtCase.verdict_pdf}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center px-3 py-2 text-sm text-blue-400 hover:text-blue-300 transition-colors duration-200"
          >
            <DocumentTextIcon className="h-4 w-4 mr-1.5" />
            Open Verdict PDF
            <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-blue-500/10 text-xs">
              {courtCase.num_pages} {courtCase.num_pages === 1 ? 'page' : 'pages'}
            </span>
          </a>
        </div>
      </div>
    </div>
  );
}; 