'use client';

import { useState, useMemo } from 'react';
import { CourtCaseCard } from '@/components/CourtCaseCard';
import courtCasesData from '@/data/court_cases.json';
import { CourtCase } from '@/types/CourtCase';
import { Slider, Pagination } from '@mui/material';

type SortOrder = 'none' | 'newest' | 'oldest' | 'longest' | 'shortest';

interface TagStats {
  cases_per_tag: { [key: string]: number };
  ordered_tags: string[];
}

interface CourtCasesData {
  cases: CourtCase[];
  tag_stats: TagStats;
}

export default function Home() {
  const [includedTags, setIncludedTags] = useState<string[]>([]);
  const [excludedTags, setExcludedTags] = useState<string[]>([]);
  const [selectedAreas, setSelectedAreas] = useState<string[]>([]);
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest');
  const [draggedTag, setDraggedTag] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [casesPerPage] = useState(12); // Show 12 cases per page
  
  // Ensure we have the correct data structure
  const data = useMemo(() => {
    const rawData = courtCasesData as any;
    return {
      cases: Array.isArray(rawData) ? rawData : (rawData.cases || []),
      tag_stats: rawData.tag_stats || { cases_per_tag: {}, ordered_tags: [] }
    } as CourtCasesData;
  }, []);
  
  // Calculate the available year range from the data
  const { minYear, maxYear } = useMemo(() => {
    const years = data.cases
      .filter(c => c.date)
      .map(c => parseInt(c.date!.split('-')[0]));

    if (years.length === 0) {
      return {
        minYear: 2000,
        maxYear: new Date().getFullYear()
      };
    }

    return {
      minYear: Math.min(...years),
      maxYear: Math.max(...years)
    };
  }, [data.cases]);
  
  const [yearRange, setYearRange] = useState<[number, number]>([minYear, maxYear]);

  // Helper function to get visible tags for a case
  const getVisibleTags = (courtCase: CourtCase): string[] => {
    if (!courtCase.tags || !courtCase.keyword_counts) return [];

    const totalMentions = Object.values(courtCase.keyword_counts).reduce((a, b) => a + b, 0);
    const maxCount = Math.max(...Object.values(courtCase.keyword_counts));

    return courtCase.tags.filter(tag => {
      const count = courtCase.keyword_counts[tag];
      const relativeThreshold = count / totalMentions >= 0.05;
      const absoluteThreshold = count >= 3 || count / maxCount >= 0.2;
      return relativeThreshold && absoluteThreshold;
    });
  };

  // Get unique visible tags from all cases, maintaining the order from tag_stats
  const allTags = useMemo(() => {
    const visibleTagsSet = new Set(
      data.cases.flatMap(c => getVisibleTags(c))
    );
    
    // Get all visible tags and sort them alphabetically
    return Array.from(visibleTagsSet).sort((a, b) => 
      a.localeCompare(b, 'sv')  // Use Swedish locale for correct sorting of å, ä, ö
    );
  }, [data]);

  // Get unique areas
  const areas = useMemo(() => 
    Array.from(new Set(data.cases.map(c => c.area))).sort()
  , [data.cases]);

  // Calculate filtered cases for each filter type independently
  const yearFilteredCases = useMemo(() => {
    return data.cases.filter(courtCase => {
      const year = courtCase.date ? parseInt(courtCase.date.split('-')[0]) : null;
      return !year ? false : (year >= yearRange[0] && year <= yearRange[1]);
    });
  }, [data.cases, yearRange]);

  const tagFilteredCases = useMemo(() => {
    return data.cases.filter(courtCase => {
      const visibleTags = getVisibleTags(courtCase);
      
      // Check if case has all included tags
      const includesMatch = includedTags.length === 0 || 
        includedTags.every((tag: string) => visibleTags.includes(tag));
      
      // Check if case has none of the excluded tags
      const excludesMatch = excludedTags.length === 0 ||
        !excludedTags.some((tag: string) => visibleTags.includes(tag));

      return includesMatch && excludesMatch;
    });
  }, [data.cases, includedTags, excludedTags]);

  const areaFilteredCases = useMemo(() => {
    return data.cases.filter(courtCase => {
      return selectedAreas.length === 0 || selectedAreas.includes(courtCase.area);
    });
  }, [data.cases, selectedAreas]);

  // Filter and sort court cases
  const filteredCases = useMemo(() => {
    // First deduplicate cases based on court_ids
    const uniqueCases = data.cases.reduce((acc: CourtCase[], current) => {
      const isDuplicate = acc.some(item => 
        item.court_ids.some(id => current.court_ids.includes(id))
      );
      if (!isDuplicate) {
        acc.push(current);
      }
      return acc;
    }, []);

    return uniqueCases
      .filter((courtCase) => {
        const visibleTags = getVisibleTags(courtCase);
        
        // Check if case has all included tags
        const includesMatch = includedTags.length === 0 || 
          includedTags.every(tag => visibleTags.includes(tag));
        
        // Check if case has none of the excluded tags
        const excludesMatch = excludedTags.length === 0 ||
          !excludedTags.some(tag => visibleTags.includes(tag));

        // Check if case is in selected areas (if any areas are selected)
        const areaMatches = selectedAreas.length === 0 || selectedAreas.includes(courtCase.area);

        // Check if case is within selected year range
        const year = courtCase.date ? parseInt(courtCase.date.split('-')[0]) : null;
        const yearMatches = !year ? false : (year >= yearRange[0] && year <= yearRange[1]);

        return includesMatch && excludesMatch && areaMatches && yearMatches;
      })
      .sort((a, b) => {
        if (sortOrder === 'none') return 0;
        
        if (sortOrder === 'longest' || sortOrder === 'shortest') {
          const multiplier = sortOrder === 'longest' ? -1 : 1;
          return (a.num_pages - b.num_pages) * multiplier;
        }
        
        // Handle cases where dates might be missing
        if (!a.date) return sortOrder === 'newest' ? 1 : -1;
        if (!b.date) return sortOrder === 'newest' ? -1 : 1;
        
        // Compare dates
        const comparison = a.date.localeCompare(b.date);
        return sortOrder === 'newest' ? -comparison : comparison;
      })
  }, [data.cases, includedTags, excludedTags, selectedAreas, yearRange, sortOrder]);

  // Get available tags that would match at least one case with current filters
  const availableTags = useMemo(() => {
    // Get cases that match current filters except tags
    const casesMatchingOtherFilters = data.cases.filter(courtCase => {
      // Check if case is in selected areas
      const areaMatches = selectedAreas.length === 0 || selectedAreas.includes(courtCase.area);

      // Check if case is within selected year range
      const year = courtCase.date ? parseInt(courtCase.date.split('-')[0]) : null;
      const yearMatches = !year ? false : (year >= yearRange[0] && year <= yearRange[1]);

      return areaMatches && yearMatches;
    });

    // For each tag, check if it would match any cases when combined with current included/excluded tags
    const tagsWithMatches = new Set(
      casesMatchingOtherFilters
        .filter(courtCase => {
          const visibleTags = getVisibleTags(courtCase);
          
          // Check if case matches current tag filters
          const includesMatch = includedTags.length === 0 || 
            includedTags.every(tag => visibleTags.includes(tag));
          
          const excludesMatch = excludedTags.length === 0 ||
            !excludedTags.some(tag => visibleTags.includes(tag));

          return includesMatch && excludesMatch;
        })
        .flatMap(courtCase => getVisibleTags(courtCase))
    );

    // Return alphabetically sorted available tags
    return Array.from(tagsWithMatches)
      .filter(tag => 
        !includedTags.includes(tag) && 
        !excludedTags.includes(tag)
      )
      .sort((a, b) => a.localeCompare(b, 'sv'));  // Swedish locale for å, ä, ö
  }, [data, includedTags, excludedTags, selectedAreas, yearRange]);

  const handleTagToggle = (tag: string) => {
    // If tag is in excluded, remove it from there
    if (excludedTags.includes(tag)) {
      setExcludedTags(prev => prev.filter(t => t !== tag));
      return;
    }
    
    // If tag is in included, remove it from there
    if (includedTags.includes(tag)) {
      setIncludedTags(prev => prev.filter(t => t !== tag));
      return;
    }
    
    // If tag is not in either, add it to included
    setIncludedTags(prev => [...prev, tag]);
  };

  const handleDragStart = (tag: string) => {
    setDraggedTag(tag);
  };

  const handleDragEnd = () => {
    setDraggedTag(null);
  };

  const handleDrop = (targetSection: 'include' | 'exclude') => {
    if (!draggedTag) return;

    // Remove from both sections first
    setIncludedTags(prev => prev.filter(t => t !== draggedTag));
    setExcludedTags(prev => prev.filter(t => t !== draggedTag));

    // Add to target section
    if (targetSection === 'include') {
      setIncludedTags(prev => [...prev, draggedTag]);
    } else {
      setExcludedTags(prev => [...prev, draggedTag]);
    }
  };

  const handleAreaToggle = (area: string) => {
    setSelectedAreas(prev => 
      prev.includes(area)
        ? prev.filter(a => a !== area)
        : [...prev, area]
    );
  };

  const handleSortChange = (order: SortOrder) => {
    setSortOrder(order);
  };

  const handleYearRangeChange = (_event: Event, newValue: number | number[]) => {
    setYearRange(newValue as [number, number]);
  };

  const handleReset = () => {
    setIncludedTags([]);
    setExcludedTags([]);
    setSelectedAreas([]);
    setSortOrder('newest');
    setYearRange([minYear, maxYear]);
  };

  // Get current page cases
  const indexOfLastCase = currentPage * casesPerPage;
  const indexOfFirstCase = indexOfLastCase - casesPerPage;
  const currentCases = filteredCases.slice(indexOfFirstCase, indexOfLastCase);
  const totalPages = Math.ceil(filteredCases.length / casesPerPage);

  // Handle page change
  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setCurrentPage(value);
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
          DomKollen
        </h1>

        <div className="flex flex-col gap-6 mb-8">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Sort by:
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleSortChange('newest')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors
                  ${sortOrder === 'newest'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
              >
                Newest First
              </button>
              <button
                onClick={() => handleSortChange('oldest')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors
                  ${sortOrder === 'oldest'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
              >
                Oldest First
              </button>
              <button
                onClick={() => handleSortChange('longest')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors
                  ${sortOrder === 'longest'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
              >
                Most Pages
              </button>
              <button
                onClick={() => handleSortChange('shortest')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors
                  ${sortOrder === 'shortest'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
              >
                Fewest Pages
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Filter by year:
              </label>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {yearRange[0]} - {yearRange[1]}
              </div>
            </div>
            <div className="px-1 py-4">
              <Slider
                value={yearRange}
                onChange={handleYearRangeChange}
                min={minYear}
                max={maxYear}
                step={1}
                disableSwap
                sx={{
                  height: 2,
                  padding: '15px 0',
                  '& .MuiSlider-thumb': {
                    height: 14,
                    width: 14,
                    backgroundColor: '#fff',
                    border: '2px solid rgb(59, 130, 246)',
                    '&:focus, &:hover, &.Mui-active': {
                      boxShadow: 'none',
                      '@media (hover: none)': {
                        boxShadow: 'none',
                      },
                    },
                    '&:before': {
                      boxShadow: 'none',
                    },
                  },
                  '& .MuiSlider-track': {
                    height: 2,
                    backgroundColor: 'rgb(59, 130, 246)',
                  },
                  '& .MuiSlider-rail': {
                    height: 2,
                    backgroundColor: 'rgb(209, 213, 219)',
                  },
                  '& .MuiSlider-valueLabel': {
                    display: 'none',
                  },
                  '@media (pointer: coarse)': {
                    '& .MuiSlider-thumb': {
                      height: 20,
                      width: 20,
                      '&:before': {
                        height: 30,
                        width: 30,
                        marginLeft: -15,
                        marginTop: -15,
                      },
                    },
                  },
                }}
              />
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Filter by tags:
            </label>
            
            {/* Available tags */}
            <div className="flex flex-wrap gap-2">
              {availableTags.map((tag) => (
                <div
                  key={tag}
                  draggable
                  onDragStart={() => handleDragStart(tag)}
                  onDragEnd={handleDragEnd}
                  onClick={() => handleTagToggle(tag)}
                  className="group px-3 py-1 rounded-full text-sm font-medium bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors cursor-move"
                >
                  {tag}
                </div>
              ))}
            </div>

            {/* Tag filter sections */}
            <div className="grid grid-cols-2 gap-4">
              {/* Includes section */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  handleDrop('include');
                }}
                className="min-h-[100px] p-4 rounded-lg border-2 border-emerald-500/20 bg-emerald-500/5"
              >
                <h3 className="text-sm font-medium text-emerald-600 dark:text-emerald-400 mb-2">
                  Includes (drag here to include)
                </h3>
                <div className="flex flex-wrap gap-2">
                  {includedTags.map((tag) => (
                    <div
                      key={tag}
                      draggable
                      onDragStart={() => handleDragStart(tag)}
                      onDragEnd={handleDragEnd}
                      onClick={() => handleTagToggle(tag)}
                      className="px-3 py-1 rounded-full text-sm font-medium bg-emerald-500 text-white cursor-move hover:bg-emerald-600 transition-colors"
                    >
                      {tag}
                    </div>
                  ))}
                </div>
              </div>

              {/* Excludes section */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  handleDrop('exclude');
                }}
                className="min-h-[100px] p-4 rounded-lg border-2 border-red-500/20 bg-red-500/5"
              >
                <h3 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">
                  Excludes (drag here to exclude)
                </h3>
                <div className="flex flex-wrap gap-2">
                  {excludedTags.map((tag) => (
                    <div
                      key={tag}
                      draggable
                      onDragStart={() => handleDragStart(tag)}
                      onDragEnd={handleDragEnd}
                      onClick={() => handleTagToggle(tag)}
                      className="px-3 py-1 rounded-full text-sm font-medium bg-red-500 text-white cursor-move hover:bg-red-600 transition-colors"
                    >
                      {tag}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Filter by areas:
            </label>
            <div className="flex flex-wrap gap-2">
              {areas.map((area) => (
                <button
                  key={area}
                  onClick={() => handleAreaToggle(area)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors
                    ${selectedAreas.includes(area)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                    }`}
                >
                  {area}
                </button>
              ))}
            </div>
          </div>

          {/* Show filtered count below all filters */}
          <div className="text-sm text-gray-600 dark:text-gray-400 text-center border-t pt-4">
            {filteredCases.length === data.cases.length ? (
              'Showing all cases'
            ) : (
              `Showing ${filteredCases.length} of ${data.cases.length} cases`
            )}
          </div>

          {/* Reset button */}
          {(includedTags.length > 0 || excludedTags.length > 0 || selectedAreas.length > 0 || 
            sortOrder !== 'none' || yearRange[0] !== minYear || yearRange[1] !== maxYear) && (
            <button
              onClick={handleReset}
              className="mx-auto px-4 py-2 rounded-full text-sm font-medium bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
              </svg>
              Reset all filters
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {currentCases.map((courtCase) => (
            <CourtCaseCard key={courtCase.verdict_pdf} courtCase={courtCase} />
          ))}
        </div>

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex justify-center mt-8">
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={handlePageChange}
              variant="outlined"
              shape="rounded"
              size="large"
              sx={{
                '& .MuiPaginationItem-root': {
                  color: 'white',
                  borderColor: 'rgba(255, 255, 255, 0.23)',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  },
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    },
                  },
                },
              }}
            />
          </div>
        )}

        {/* Show total results count */}
        <div className="text-center text-gray-400 mt-4">
          Showing {indexOfFirstCase + 1}-{Math.min(indexOfLastCase, filteredCases.length)} of {filteredCases.length} cases
        </div>
      </div>
    </main>
  );
} 